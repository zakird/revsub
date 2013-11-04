
nv.addGraph(function() {
  var chart = nv.models.scatterChart()
                .color(d3.scale.category10().range());

  chart.xAxis.tickFormat(d3.format('.02f')).axisLabel("Score")
  chart.yAxis.tickFormat(d3.format('.02f')).axisLabel("Percentage of Students")
  chart.forceX([0,3])
  chart.forceY([0,1])
  d3.select('#chart svg')
      .datum(getData("score_cdf?course_id=1"))
      .call(chart);

  nv.utils.windowResize(chart.update);

  return chart;
});

nv.addGraph(function() {
  var chart = nv.models.scatterChart();

  chart.xAxis.tickFormat(d3.format('.02f')).axisLabel("Score")
  chart.yAxis.tickFormat(d3.format('.02f')).axisLabel("Percentage of Students")
  chart.forceX([0,3])
  chart.forceY([0,1])
  d3.select('#chart2 svg')
      .datum(getData("scores_given_cdf?course_id=1"))
      .call(chart);

  nv.utils.windowResize(chart.update);

  return chart;
});


function getData(name) {
    var json = null;
    $.ajax({
        'async': false,
        'global': false,
        'url': name,
        'dataType': "json",
        'success': function (data) {
            json = data;
        }
    });
    return json.r;
}; 


