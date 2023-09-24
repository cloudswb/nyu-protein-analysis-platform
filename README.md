## Background



## Code structure

- proteindc-website-deploy
  - deploy #部署脚本和文件
    - lambda #部署用到的lambda代码
    - data_init #数据初始化
    - proteindc_notebook #用于把nodebook的脚本初始化的脚本
    - config.py #配置文件
  - layers #lambda依赖的layer信息
  - requirements.txt #依赖的python包的安装脚本
  - app.py #应用程序执行脚本
- web #前端代码

## How to deploy

refer to: https://cloudswb.notion.site/Uniprot-Cytoscape-js-Amazon-Npetune-1c719838a49f41408ef479d5db326308
