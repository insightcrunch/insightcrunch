---
layout: post
title: "Interacting with Enhanced Data Interpretations"
date: 2020-07-13
categories: ["Analytics"]
tags: ["Tableau"]
excerpt: "As we traverse one of the most uncertain times in our history to a new future where things may never allow us to be the same, informed decision-making in the age of data analytics can go a long way ..."
image: "/assets/images/technology-industry-analysis-insightcrunch.webp"
reading_time: 2
author: "Insight Crunch Team"
last_updated: 2026-03-15
---
As we traverse one of the most uncertain times in our history to a new future where things may never allow us to be the same, informed decision-making in the age of data analytics can go a long way to help see the unseen often right infront of us. Correlation, causality, related dimensions that otherwise would be difficult to interpret easily surfaces up when seen from the right context.

![](/assets/images/technology-industry-analysis-insightcrunch.webp)
West Bengal COVID Data

In the eastern part of the 2ndmost populous country of the world in India, lies the diverse state of [West Bengal](https://en.wikipedia.org/wiki/West_Bengal) with a population of nearly 100 million and land area of 34,267 mi². To put that into perspective, that translates to nearly ¼ of the US population in an area that is ¹⁄₁₁₀ the size of US land area, a population density of 28 times more. Upholding the safety protocols at this juncture will need prolific planning and execution, as we all try to overcome the Coronavirus pandemic together.

The below schematics has been created using data from [Wikipedia](https://en.wikipedia.org/wiki/COVID-19_pandemic_in_West_Bengal#District_wise_cases_&_Graphs) which currently holds active cases counts as of mid-June 2020. The intensity of colors represents the amount of active cases in comparison to other districts, almost always proportionate with the [population](https://en.wikipedia.org/wiki/West_Bengal#Districts) in the respective district. The population figures pertain to Census 2011 however would provide a rough comparative summary of the districts. Deselecting the toppers from the District dropdown below starts to reveal more distinguishable comparative shades of the districts.

[
![Population and Active Cases by District5/29/2020 3:07:51 PM ](/assets/images/technology-industry-analysis-insightcrunch.webp)
](#)                                       var divElement = document.getElementById('viz1660269020041');                    var vizElement = divElement.getElementsByTagName('object')[0];                    vizElement.style.width='100%';vizElement.style.height=(divElement.offsetWidth*0.75)+'px';                    var scriptElement = document.createElement('script');                    scriptElement.src = 'https://public.tableau.com/javascripts/api/viz_v1.js';                    vizElement.parentNode.insertBefore(scriptElement, vizElement);                

A geomap creation with overlaying useful dimensions helps strengthen the visualization. It took some digging around and fine-tuning as there wasn’t a readily available dataset with accurate latitudes and longitudes to plot the required districts. Now along with the headquarters of each district and the containment zone coloring as of June [data](https://en.wikipedia.org/wiki/COVID-19_pandemic_in_West_Bengal#District_wise_cases_&_Graphs), we have an enhanced visibility of the current scenario.

[
![Population and Zones by District5/29/2020 3:07:51 PM ](/assets/images/technology-industry-analysis-insightcrunch.webp)
](#)                                       var divElement = document.getElementById('viz1660269065809');                    var vizElement = divElement.getElementsByTagName('object')[0];                    vizElement.style.width='100%';vizElement.style.height=(divElement.offsetWidth*0.75)+'px';                    var scriptElement = document.createElement('script');                    scriptElement.src = 'https://public.tableau.com/javascripts/api/viz_v1.js';                    vizElement.parentNode.insertBefore(scriptElement, vizElement);                

The charts above are best viewed in a bigger screen area. For the latest figures, we can find them in these curated sites for [West Bengal](https://www.wbhealth.gov.in/pages/corona/bulletin/) and [India](https://www.covid19india.org/).

![](/assets/images/technology-industry-analysis-insightcrunch.webp)