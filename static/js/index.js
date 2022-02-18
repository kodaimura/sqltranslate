
document.getElementById("translate").addEventListener("click", () => {
	const sql = document.getElementById("sql").value
	fetch("/sql", {
		method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({sql})
    })
    .then(response => {return response.json()})
    .then(data => {
    	document.getElementById('result').innerHTML = data.result
    })
    .catch(console.error);
})