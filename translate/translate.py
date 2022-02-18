from .parser import parse

def translate(sql):
	sql_ast = parse(sql)
	if type(sql_ast) == Exception:
		return str(sql_ast)
	else:
		return translate_select(sql_ast) + '。'


def translate_select(sql_ast):
	ret = ''
	complement_word = ''

	for ast in sql_ast:
		if ast == 'UNION':
			ret += '。その結果に、'
			complement_word = 'したレコードを結合'
		elif ast == 'ALL':
			complement_word += '(重複レコードを含む)'
		else:
			ret += translate_select_statement(ast)
			ret += complement_word
			complement_word = ''

	return ret


def translate_select_statement(ast):
	s = translate_select_clause(ast[0])
	f = translate_from_clause(ast[1])
	w = translate_where_clause(ast[2])
	o = translate_order_by_clause(ast[3])

	return f + w + o + s


def translate_select_clause(ast):
	ret = ''
	columns = ast['columns']

	for col in columns:
		ret += '、'
		if col == '*':
			ret = '全ての項目'
		elif col['type'] == 'column':
			if col['table']:
				ret += '{}テーブルの'.format(col['table'])
			if col['column']:
				ret += '{}'.format(col['column'])
			if col['alias']:
				ret += '(列別名: {})'.format(col['alias'])
		elif col['type'] == 'number':
			if col['value']:
				ret += '{}列目'.format(col['value'])
			if col['alias']:
				ret += '(列別名: {})'.format(col['alias'])
		else:
			if col['value']:
				ret += '固定値{}'.format(col['value'])
			if col['alias']:
				ret += '(列別名: {})'.format(col['alias'])

	return ret + 'の抽出'


def translate_from_clause(ast):
	ret = ''
	tables = ast['tables']

	for table in tables:
		if table['type'] == 'records':
			ret += '{}したレコード'.format(translate_select(table['records']))
		else:
			ret += '{}テーブル'.format(table['table'])

		if table['alias']:
			ret += '(別名: {})、'.format(table['alias'])
		else:
			ret += '、'

	return ret[:-1] + 'から'


def translate_where_clause(ast):
	if not ast:
		return ''

	return translate_conditions(ast['conditions']) + 'という条件で'


def translate_conditions(conditions):
	ret = ''
	complement_word = ''

	for item in conditions:
		if item == 'AND':
			ret += 'かつ、'
		elif item == 'OR':
			ret += 'または、'
		elif item == '=':
			ret += 'が'
			complement_word = 'と等しい'
		elif item in ['<>, !=']:
			ret += 'が'
			complement_word = 'と異なる'
		elif item == '<':
			ret += 'が'
			complement_word = 'より小さい'  
		elif item == '>':
			ret += 'が'
			complement_word = 'より大きい'
		elif item == '<=':
			ret += 'が'
			complement_word = '以下'
		elif item == '>=':
			ret += 'が'
			complement_word = '以上'
		elif item == 'IN':
			ret += 'が'
			complement_word = 'に含まれる' if complement_word != 'では無い' else 'に含まれない'
		elif item == 'EXISTS':
			complement_word = 'にデータが存在する' if complement_word != 'では無い' else 'にデータが存在しない'
		elif item == 'NOT':
			complement_word = 'では無い'
		elif item in ['+', '-', '*', '/']:
			ret += item
		else:
			ret += translate_condition_item(item) + complement_word
			complement_word = ''

	return ret


def translate_condition_item(ast):
	if ast['type'] == 'records':
		return translate_select(ast['records'])
	elif ast['type'] == 'conditions':
		return translate_conditions(ast['conditions'])
	elif ast['type'] in ['number', 'string']:
		return translate_value(ast)
	else:
		return translate_column(ast)


def translate_value(ast):
	ret = ''
	return ast['value']


def translate_column(ast):
	ret = ''
	
	if ast['table']:
		ret += '{}テーブルの'.format(ast['table'])
	if ast['column']:
		ret += '{}'.format(ast['column'])

	return ret


def translate_asc_desc(x):
	return '昇順' if x == 'ASC' else '降順'


def translate_order_by_clause(ast):
	if not ast:
		return ''

	ret = ''
	columns = ast['BY']
	for item in columns:
		ret += '、'
		if item['type'] == 'number':
			ret += '{}列目の{}'.format(item['value'], translate_asc_desc(item['order']))
		else:
			if item['table']:
				ret += '{}テーブルの'.format(item['table'])
			if item['column']:
				ret += '{}の{}'.format(item['column'], translate_asc_desc(item['order']))

	return ret + 'にソートして'

