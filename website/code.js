/* global Promise, fetch, window, cytoscape, document, tippy, _ */


searchBtn = document.getElementById('btnSearchProtein');

function proteinSearchClicked(e){
  proteinIdInput = document.getElementById('proteinId');
  networkdepthSlide = document.getElementById('networkdepth');

  if(proteinIdInput.value == ""){
    alert("Please input protein AC information first.")
    return;
  }

  // alert(proteinIdInput.value)
  // alert(networkdepthSlide.value)
  searchAndLoadNetwork(proteinIdInput.value, networkdepthSlide.value)
}

function searchAndLoadNetwork(proteinId, depth)
{
  const myRequest = new Request("https://0h95n3oud4.execute-api.us-east-1.amazonaws.com/test/ognetwork?ac="+proteinId+"&deep="+depth, {
    method: "GET",
    headers: {
      'Content-Type': 'application/json',
    },
    mode: "cors",
    cache: "default",
  });

  Promise.all([
    fetch('cy-style.json')
      .then(function(res) {
        return res.json();
      }),
    fetch(myRequest)
      .then(function(res) {
        return res.json();
      })
  ])
    .then(function(dataArray) {
      
      var cy = window.cy = cytoscape({
        container: document.getElementById('cy'),
        style: dataArray[0],
        elements: dataArray[1],
        layout: { name: 'random' }
      });

      cy.nodes().forEach(function(n){
        var g = n.data('name');
  
        var $links = [
          {
            name: 'UniProt search',
            url: 'http://www.uniprot.org/uniprot/?query='+ g
          },
        ].map(function( link ){
          return h('a', { target: '_blank', href: link.url, 'class': 'tip-link' }, [ t(link.name) ]);
        });
  
        var tippy = makeTippy(n, h('div', {}, $links));
  
        n.data('tippy', tippy);
  
        n.on('click', function(e){
          tippy.show();
  
          cy.nodes().not(n).forEach(hideTippy);
        });
      });

      cy.on('tap', function(e){
        if(e.target === cy){
          console.log('tap hideAllTippies')
          hideAllTippies();
        }
      });
      
      cy.on('tap', 'edge', function(e){
        hideAllTippies();
      });
      
      cy.on('zoom pan', function(e){
        hideAllTippies();
      });
  

    });

}

function removeLastCharacter(str) {
  return str.slice(0, -1);
}

function retriveAnnotationInfoClicked(e){
  
  var selectedNodesString = '';
  var selectedNodes = cy.elements('node:selected');
  var selectedNodesCount = selectedNodes.length;

  if((selectedNodesCount == 0)){
    alert('No nodes select, please select protein node first.')
    return
  }

  // 构建要传递的参数字符串，这里以逗号分隔数字为例
  selectedNodes.forEach(function(n){
    console.log(n.data)
    var nodeName = n.data('name');
    console.log(n)
    selectedNodesString += nodeName + ","

  });

  
  selectedNodesString = removeLastCharacter(selectedNodesString)

  // 构建目标页面的 URL，并将参数附加在URL后面
  const targetUrl = 'annotation.html?data=' + encodeURIComponent(selectedNodesString);

  // 使用 window.open() 打开目标页面
  window.open(targetUrl);

}



var $ = document.querySelector.bind(document);
var h = function(tag, attrs, children){
  var el = document.createElement(tag);

  Object.keys(attrs).forEach(function(key){
    var val = attrs[key];

    el.setAttribute(key, val);
  });

  children.forEach(function(child){
    el.appendChild(child);
  });

  return el;
};

var t = function(text){
  var el = document.createTextNode(text);

  return el;
};
var cyStyle = []
var cyElements = []
var cy = window.cy = cytoscape({
  container: document.getElementById('cy'),
  style: cyStyle,
  elements: cyElements,
  layout: { name: 'random' }
});
var params = {
  name: 'cola',
  nodeSpacing: 5,
  edgeLengthVal: 15,
  networkdeep: 3,
  animate: true,
  randomize: false,
  maxSimulationTime: 1500
};
var layout = makeLayout();

layout.run();

var $btnParam = h('div', {
  'class': 'param'
}, []);

var $config = $('#config');

$config.appendChild( $btnParam );

var sliders = [
  {
    label: 'Edge length',
    param: 'edgeLengthVal',
    min: 1,
    max: 200
  },

  {
    label: 'Node spacing',
    param: 'nodeSpacing',
    min: 1,
    max: 50
  }
];

var buttons = [
  {
    label: h('span', { 'class': 'fa fa-random' }, []),
    layoutOpts: {
      randomize: true,
      flow: null
    }
  },

  {
    label: h('span', { 'class': 'fa fa-long-arrow-down' }, []),
    layoutOpts: {
      flow: { axis: 'y', minSeparation: 30 }
    }
  }
];

sliders.forEach( makeSlider );

buttons.forEach( makeButton );

function makeLayout( opts ){
  params.randomize = false;
  params.edgeLength = function(e){ return params.edgeLengthVal / e.data('weight'); };

  for( var i in opts ){
    params[i] = opts[i];
  }

  return cy.layout( params );
}

function makeSlider( opts ){
  var $input = h('input', {
    id: 'slider-'+opts.param,
    type: 'range',
    min: opts.min,
    max: opts.max,
    step: 1,
    value: params[ opts.param ],
    'class': 'slider'
  }, []);

  var $param = h('div', { 'class': 'param' }, []);

  var $label = h('label', { 'class': 'label label-default', for: 'slider-'+opts.param }, [ t(opts.label) ]);

  $param.appendChild( $label );
  $param.appendChild( $input );

  $config.appendChild( $param );

  var update = _.throttle(function(e){
    console.log($input.value)
    console.log(e.target.id)
    
    params[ opts.param ] = $input.value;

    layout.stop();
    layout = makeLayout();
    layout.run();
  }, 1000/30);

  // $input.addEventListener('input', update);
  $input.addEventListener('change', update);
}

function makeButton( opts ){
  var $button = h('button', { 'class': 'btn btn-default' }, [ opts.label ]);

  $btnParam.appendChild( $button );

  $button.addEventListener('click', function(){
    layout.stop();

    if( opts.fn ){ opts.fn(); }

    layout = makeLayout( opts.layoutOpts );
    layout.run();
  });
}

var makeTippy = function(node, html){
  return tippy( node.popperRef(), {
    html: html,
    trigger: 'manual',
    arrow: true,
    placement: 'bottom',
    hideOnClick: false,
    interactive: true
  } ).tooltips[0];
};

var hideTippy = function(node){
  var tippy = node.data('tippy');

  if(tippy != null){
    tippy.hide();
  }
};

var hideAllTippies = function(){
  
  cy.nodes().forEach(hideTippy);
};



$('#config-toggle').addEventListener('click', function(){
  $('body').classList.toggle('config-closed');

  cy.resize();
});

