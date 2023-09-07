import json

def update_website_config(api_url):

    file_path = '/Users/zhangkap/aws/client/nyu/code/nyu-protein-analysis-platform/web/config.js'
    api_url = api_url

    js_config_content = {
        "apiEndpointUrl": api_url
    }

    js_config_content_string = json.dumps(js_config_content, indent=2)

    # Open the file in append mode ('a')
    with open(file_path, 'w') as file:
        file.write("\n")  # Add a newline before appending
        file.write(f"const config ={js_config_content_string}")
        file.write("\n") 
        file.write("export default config;")

    print(f'Content has been appended to the file "{file_path}".')

value1 = '111'
value2 = '222'
api_url = f'https://${Token[TOKEN.1021]}.execute-api.us-east-1.${Token[AWS.URLSuffix.3]}/${Token[TOKEN.1029]}/'
update_website_config(api_url)