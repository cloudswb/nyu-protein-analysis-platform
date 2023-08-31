import json
import os
from SPARQLWrapper import SPARQLWrapper, JSON

# Set up the SPARQL endpoint URL
sparql_endpoint = os.environ['SPARQL_ENDPOINT']
# sparql_endpoint = 'https://nyu-neptune-instance-1.cnfpwwtkftli.us-east-1.neptune.amazonaws.com:8182/sparql'
sparql = SPARQLWrapper(sparql_endpoint)

# Write and execute a SPARQL query

functionQuery = """
PREFIX up: <http://purl.uniprot.org/core/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX uniprotkb: <http://purl.uniprot.org/uniprot/>

SELECT 
    (CONCAT(SUBSTR(STR(?protein), 33)) AS ?uniprot)

	?protein
?annotation
?comment


WHERE
{{
    BIND (uniprotkb:{uniprotkb} AS ?protein)
    ?protein a up:Protein ;
            up:annotation ?annotation .
    
    ?annotation rdf:type up:Function_Annotation ;
            rdfs:comment ?comment .

}}
"""

goTermQuery = """
PREFIX up: <http://purl.uniprot.org/core/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX uniprotkb: <http://purl.uniprot.org/uniprot/>

SELECT 
    (CONCAT(SUBSTR(STR(?protein), 33)) AS ?uniprot)
	?protein
	?goTerm


WHERE
{{
    BIND (uniprotkb:{uniprotkb} AS ?protein)
    ?protein up:classifiedWith ?goTerm .
}}
"""

sequenceQuery = """
PREFIX up: <http://purl.uniprot.org/core/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX uniprotkb: <http://purl.uniprot.org/uniprot/>

SELECT 
    (CONCAT(SUBSTR(STR(?protein), 33)) AS ?uniprot)

	?protein
	?sequence
    ?simple_sequence


WHERE
{{
    BIND (uniprotkb:{uniprotkb} AS ?protein)

    ?protein a up:Protein ;
            up:sequence ?sequence .

  	?sequence rdf:value ?simple_sequence .
}}
"""

def queryNeptune(query):
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    # Process and print the query results
    for result in results["results"]["bindings"]:
        print(result)
    
    return results["results"]["bindings"]

def lambda_handler(event, context):
    
    ac = event['queryStringParameters']['ac'];
    
    if(ac == ""):
        return {
            'statusCode': 500,
            'body': 'ac is needed.' 
        }
    
    print('functionQuery:')
    functionQueryFormat = functionQuery.format(uniprotkb = ac)
    functionQueryResult = queryNeptune(functionQueryFormat)

    print('goTermQuery:')
    goTermQueryFormat = goTermQuery.format(uniprotkb = ac)
    goTermQueryResult = queryNeptune(goTermQueryFormat)

    print('sequenceQuery:')
    sequenceQueryFormat = sequenceQuery.format(uniprotkb = ac)
    sequenceQueryResult = queryNeptune(sequenceQueryFormat)

    response = {
            "statusCode": 200,
            "headers": {
                'Access-Control-Allow-Origin': '*'
            },
            'body':json.dumps({ 'function': functionQueryResult , 'goTerm': goTermQueryResult, 'sequence': sequenceQueryResult })
        }
    
    return response
    # TODO implement
    # return {
    #     'statusCode': 200,
    #     'body':json.dumps({ 'function': functionQueryResult , 'goTerm': goTermQueryResult, 'sequence': sequenceQueryResult }) 
    # }

