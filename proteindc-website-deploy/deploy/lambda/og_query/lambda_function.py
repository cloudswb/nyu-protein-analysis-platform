import sys
import logging
import pymysql
import json
import os

# rds settings
user_name = os.environ['USER_NAME']
password = os.environ['PASSWORD']
rds_host = os.environ['RDS_HOST']
db_name = os.environ['DB_NAME']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create the database connection outside of the handler to allow connections to be
# re-used by subsequent function invocations.
try:
    conn = pymysql.connect(host=rds_host, user=user_name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit()

logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")

def check_exist_node(nodelist, node) :

    for row in nodelist:
        if row['data']['id'] == node:
            return True
            
    return False
    
def check_exist_edge(edgeList, edgeItem) :

    for edge in edgeList:
        if edge['data']['source'] == edgeItem['data']['source'] and edge['data']['target'] == edgeItem['data']['target'] :
            return True
            
    return False
    
def retrive_network(conn, ac, nodes, edges, depth, group):

    item_count = 0
    with conn.cursor() as cur:
        # cur.execute("create table if not exists Customer ( CustID  int NOT NULL, Name varchar(255) NOT NULL, PRIMARY KEY (CustID))")
        # cur.execute(sql_string)
        # conn.commit()
        sql = "select * from edge where source = %s"
        params = (ac,)
        
        cur.execute(sql, params)
        
        # json_data = json.dumps(cur.fetchall())
        # print(json_data)
        
        for row in cur:
            
            logger.info("The following items have been retrived from the database:")
            newEdge = { "data": { "source": row[1], "target": row[2], "weight": row[3], "depth": depth, "group": group } }
            print(newEdge)
            if not check_exist_edge(edges, newEdge):
                edges.append(newEdge)
            
            # logger.info("edges:", edges)
            
            
            if not check_exist_node(nodes, row[1]):
                print('append source node: ', row[1])
                nodes.append({ "data" : { 'id': row[1], 'name': row[1], 'group': group}})
            else:
                print('already exists source node: ', row[1])
                
            if not check_exist_node(nodes, row[2]):
                print('append target node: ', row[2])
                nodes.append({ "data" : { 'id': row[2], 'name': row[2], 'group': group }})
            else:
                print('already exists target node: ', row[1])
            item_count += 1
            
            logger.info(nodes)
    
def lambda_handler(event, context):
    
    print("event---------")
    logger.info(event)
    
    # logger.info(context)
    
    """
    This function creates a new RDS database table and writes records to it
    """
    # message = event['Records'][0]['body']
    # data = json.loads(message)
    # CustID = data['CustID']
    # Name = data['Name']
    
    acValue = event['queryStringParameters']['ac']
    

    acList = acValue.split(',')
    
    nodes = []
    edges = []
    
    for ac in acList:
        print("ac", ac)
        print("len(ac)", len(ac))
        
        if len(ac) > 0:
            deep = event['queryStringParameters']['deep']
            deep = int(deep) + 1
            print('deep:', deep)
            
            for depthIndex in range(1, deep):
                print('depthIndex: ', depthIndex)
                if depthIndex == 1:
                    retrive_network(conn, ac, nodes, edges, depthIndex, ac)
                else:
                    
                    mappedEdges = [x for x in edges if x['data']['depth'] == depthIndex -1]
                    
                    print("mappedEdges")
                    print(json.dumps(mappedEdges))
                    
                    for edgeItem in mappedEdges:
                        retrive_network(conn, edgeItem['data']['target'], nodes, edges, depthIndex, ac)
                        
                conn.commit()
    
    response = {
        "statusCode": 200,
        "headers": {
            'Access-Control-Allow-Origin': '*'
        },
        "body": json.dumps({ 'nodes': nodes, 'edges': edges })
    }
    
    # print(response)
    
    return response
    
