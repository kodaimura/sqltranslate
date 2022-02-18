import re

KEYPHRASES = ['SELECT', 'FROM', 'WHERE', 'ORDER', 'UNION']
SYMBOLS = [',', '.', '(', ')', '-', '+', '*', ';', '=', '!', '<', '>']


def error_message(atom):
	return 'Syntax Error: near "{}".'.format(atom)

def list_upper_lower(ls):
	return list(map(lambda s: s.lower(), ls)) + list(map(lambda s: s.upper(), ls))

def is_valid_name(atom):
	return (atom not in list_upper_lower(KEYPHRASES + ['NOT', 'IN', 'AND', 'OR', 'EXISTS', 'ALL'])
		and re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]{0,}', atom))

def is_valid_string(atom):
	return re.fullmatch(r'^\'.*\'$', atom) or re.fullmatch(r'^".*"$', atom)

def is_valid_number(atom):
	return re.fullmatch(r'[0-9]{1,}', atom)

def is_valid_value(atom):
	return is_valid_number(atom) or is_valid_string(atom) or is_valid_name(atom)


def parse(sql):
	parser = Parser()
	return parser.parse(sql)

def divide_into_atom(sql):
	return list(
		map(
			lambda s: s.replace('[SPACE]', ' '),
			filter(
				lambda s: s!= '',
				put_space(sql).split(' '))))


def put_space(sql):
	ret = ''
	sql_len = len(sql)
	skip = False
	string_sq = False 
	string_dq = False

	for i, s in enumerate(sql):
		if s == '\n':
			continue

		if skip:
			ret += '{} '.format(s)
			skip = False
			continue

		if string_sq:
			if s == "'":
				string_sq = False
			ret += '[SPACE]' if s == ' ' else s
			continue

		if string_dq:
			if s == '"':
				string_dq = False
			ret += '[SPACE]' if s == ' ' else s
			continue

		if s == "'":
			string_sq = True
			ret += "'"

		elif s == '"':
			string_dq = True
			ret += '"'

		elif s == '<':
			if i + 1 < sql_len and sql[i + 1] in ['>', '=']:
				ret += ' {}'.format(s)
				skip = True
			else:
				ret += ' {} '.format(s)

		elif s in ['!', '>']:
			if i + 1 < sql_len and sql[i + 1] == '=':
				ret += ' {}'.format(s)
				skip = True
			else:
				ret += ' {} '.format(s)
		else:
			ret += ' {} '.format(s) if s in SYMBOLS else s

	return ret


class Parser:

	def __init__(self):
		self.atoms = []
		self.end_of_sql = [';'] 


	def parse(self, sql):
		self.atoms = divide_into_atom(sql)

		try:
			if self.atoms[-1] != ';':
				raise Exception('Syntax Error: missing ";"')
			return self.parse_select()

		except Exception as e:
			return e


	def parse_select(self):
		ret = []
		while True:
			if self.atoms[0] == self.end_of_sql[0]:
				break
				
			if self.atoms[0] in list_upper_lower(['union']):
				ret.append(self.atoms.pop(0).upper())
				if self.atoms[0] in list_upper_lower(['all']):
					ret.append(self.atoms.pop(0).upper())
			ret.append(self.parse_select_statement())

		return ret


	def parse_select_statement(self):
		ret = []
		ret.append(self.parse_select_clause())
		ret.append(self.parse_from_clause())
		ret.append(self.parse_where_clause())
		ret.append(self.parse_order_by_clause())
		return ret


	def parse_select_clause(self):
		if self.atoms[0] in list_upper_lower(['select']):
			self.atoms.pop(0)
		else:
			raise Exception(error_message(self.atoms[0]))

		ret = { 'clause': 'SELECT' }
		columns = []
		columns.append(self.parse_select_column())
		while True:
			if self.atoms[0] == ';':
				raise Exception(error_message(self.atoms[0]))
			elif self.atoms[0] in list_upper_lower(KEYPHRASES):
				break
			elif self.atoms[0] == ',':
				self.atoms.pop(0)
				columns.append(self.parse_select_column())
			else:
				raise Exception(error_message(self.atoms[0]))

		ret['columns'] = columns
		return ret


	def parse_select_column(self):
		ret = {}

		if self.atoms[0] == '*':
			return self.atoms.pop(0)
		elif is_valid_name(self.atoms[0]):
			ret = self.parse_column()
		elif is_valid_value(self.atoms[0]):
			ret = self.parse_value()
		else:
			raise Exception(error_message(self.atoms[0]))

		ret['alias'] = self.parse_alias()
		return ret


	def parse_from_clause(self):
		if self.atoms[0] in list_upper_lower(['from']):
			self.atoms.pop(0)
		else:
			raise Exception(error_message(self.atoms[0]))

		ret = { 'clause': 'FROM' }
		tables = []
		tables.append(self.parse_from_table())

		while True:
			if self.atoms[0] in list_upper_lower(KEYPHRASES):
				break
			elif self.atoms[0] == self.end_of_sql[0]:
				break
			elif self.atoms[0] == ',':
				self.atoms.pop(0)
				tables.append(self.parse_from_table())
			else:
				raise Exception(error_message(self.atoms[0]))

		ret['tables'] = tables
		return ret


	def parse_from_table(self):
		ret = {}
		if is_valid_name(self.atoms[0]):
			ret['type'] = 'table'
			ret['table'] = self.atoms.pop(0)
		elif self.atoms[0] == '(':
			if self.atoms[1] in list_upper_lower(['select']):
				ret = self.parse_bracket()
		else:
			raise Exception(error_message(self.atoms[0]))

		ret['alias'] = self.parse_alias()
		return ret


	def parse_where_clause(self):
		if self.atoms[0] not in list_upper_lower(['where']):
			return None
		self.atoms.pop(0)

		ret = { 'clause': 'WHERE' }
		ret['conditions'] = self.parse_conditions()

		return ret


	def parse_conditions(self):
		conditions = []
		is_first = True
		required_next = True

		while True:
			if self.atoms[0] in list_upper_lower(KEYPHRASES):
				break
			elif self.atoms[0] == self.end_of_sql[0]:
				break
			elif is_first and self.atoms[0] in ['+', '-']:
				conditions.append(self.atoms.pop(0))
				required_next = True
				is_first = False
			elif is_first and self.atoms[0] in list_upper_lower(['not']):
				conditions.append(self.atoms.pop(0).upper())
				required_next = True
				is_first = True
			elif is_first and self.atoms[0] in list_upper_lower(['exists']):
				conditions.append(self.atoms.pop(0).upper())
				required_next = True
				is_first = False
			elif required_next:
				required_next = False
				is_first = False
				conditions.append(self.parse_condition_item())
			elif self.atoms[0] in ['+', '-', '*', '/']:
				conditions.append(self.atoms.pop(0))
				required_next = True
				is_first = False
			elif self.atoms[0] in ['=', '<>', '!=', '<', '>', '<=', '>='] + list_upper_lower(['in']):
				conditions.append(self.atoms.pop(0).upper())
				required_next = True
				is_first = True
			elif self.atoms[0] in list_upper_lower(['and', 'or']):
				conditions.append(self.atoms.pop(0).upper())
				required_next = True
				is_first = True
			else:
				raise Exception(error_message(self.atoms[0]))

		if conditions == []:
			raise Exception(error_message(self.atoms[0]))

		return conditions


	def parse_condition_item(self):
		ret = {}

		if self.atoms[0] == '(':
			return self.parse_bracket()
		elif is_valid_name(self.atoms[0]):
			ret = self.parse_column()
		elif is_valid_value(self.atoms[0]):
			ret = self.parse_value()
		else:
			raise Exception(error_message(self.atoms[0]))

		return ret


	def parse_bracket(self):
		ret = {}

		self.end_of_sql.insert(0, ')')
		self.atoms.pop(0)

		if self.atoms[0] in list_upper_lower(['select']):
			ret['type'] = 'records'
			ret['records'] = self.parse_select()
		else:
			ret['type'] = 'conditions'
			ret['conditions'] = self.parse_conditions()

		if self.atoms[0] == ')':
			self.atoms.pop(0)
			self.end_of_sql.pop(0)
		else:
			raise Exception(error_message(self.atoms[0]))

		return ret


	def parse_order_by_clause(self):
		if self.atoms[0] not in list_upper_lower(['order']):
			return None
		self.atoms.pop(0)
		ret = { 'clause': 'ORDER' }

		if self.atoms[0] in list_upper_lower(['by']):
			self.atoms.pop(0)
		else:
			raise Exception(error_message(self.atoms[0]))

		by = []
		by.append(self.parse_order_by_column())

		while True:
			if self.atoms[0] in list_upper_lower(KEYPHRASES):
				break;
			elif self.atoms[0] == self.end_of_sql[0]:
				break
			elif self.atoms[0] == ',':
				self.atoms.pop(0)
				by.append(self.parse_order_by_column())
			else:
				raise Exception(error_message(self.atoms[0]))

		ret['BY'] = by
		return ret


	def parse_order_by_column(self):
		ret = {}

		if is_valid_number(self.atoms[0]):
			ret = self.parse_number()
		elif is_valid_name(self.atoms[0]):
			ret = self.parse_column()
		else:
			raise Exception(error_message(self.atoms[0]))

		if self.atoms[0] in list_upper_lower(['desc', 'asc']): 
			ret['order'] = self.atoms.pop(0).upper()
		else:
			ret['order'] = 'ASC'

		return ret


	def parse_column(self):
		ret = {}
		if is_valid_name(self.atoms[0]):
			ret['type'] = 'column'
			ret['table'] = None
			ret['column'] = self.atoms.pop(0)
			if self.atoms[0] == '.':
				self.atoms.pop(0)
				ret['table'] = ret['column']
				if is_valid_name(self.atoms[0]):
					ret['column'] = self.atoms.pop(0)
				else:
					raise Exception(error_message(self.atoms[0]))
		else:
			raise Exception(error_message(self.atoms[0]))

		return ret


	def parse_number(self):
		ret = {}
		if is_valid_number(self.atoms[0]):
			ret['type'] = 'number'
			ret['value'] = self.atoms.pop(0)
		else:
			raise Exception(error_message(self.atoms[0]))
			
		return ret


	def parse_string(self):
		ret = {}
		if is_valid_string(self.atoms[0]):
			ret['type'] = 'string'
			ret['value'] = self.atoms.pop(0)
		else:
			raise Exception(error_message(self.atoms[0]))
			
		return ret


	def parse_value(self):
		ret = {}
		if is_valid_number(self.atoms[0]):
			ret = self.parse_number()
		elif is_valid_string(self.atoms[0]):
			ret = self.parse_string()
		else:
			raise Exception(error_message(self.atoms[0]))
			
		return ret


	def parse_alias(self):
		if self.atoms[0] in list_upper_lower(['as']):
			self.atoms.pop(0)
			if is_valid_name(self.atoms[0]) or is_valid_string(self.atoms[0]):
				return self.atoms.pop(0)
			else:
				raise Exception(error_message(self.atoms[0]))
		elif is_valid_name(self.atoms[0]) or is_valid_string(self.atoms[0]):
			return self.atoms.pop(0)
		else:
			return None

