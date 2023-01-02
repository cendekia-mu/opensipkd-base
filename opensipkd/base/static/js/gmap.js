let map;
let btnCurrent = {lat: 0, lng: 0};
let selectedFeature = null;
let btnRemove;
let infoWindow;
let feature_data = {};
let strokeColor, strokeOpacity, strokeWeight, fillColor, fillOpacity;
let strokeColorControl, strokeOpacityControl, strokeWeightControl, fillColorControl, fillOpacityControl;
//let styleControls;
let featureStyleOptions = {
  strokeColor: "#810fcb",
  strokeOpacity: "1.0",
  strokeWeight: "3.0",
  fillColor: "#810fcb",
  fillOpacity: "0.5",
};

function initMap() {
  map = new google.maps.Map(document.getElementById("gmap"), {
    center: {lat: map_center[0], lng: map_center[1]},
    zoom: map_zoom,
    animation: google.maps.Animation.DROP,
    streetViewControl: false,
    mapTypeId: "hybrid",
    mapTypeControlOptions: {
      // style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
    },
  });

  featureStyleOptions = Object.assign(gmapDataStyle, featureStyleOptions);
  map.data.setStyle(featureStyleOptions);
  infoWindow = new google.maps.InfoWindow({
    content: "",
    ariaLabel: "Uluru",
  });

  map.data.setControls(gmapControls);

  google.maps.event.addListener(map.data, 'addfeature', function (e) {
    if (map.data.map.data.getControls() !== null) {
      let bounds = new google.maps.LatLngBounds();
      bounds = extendBound(bounds, e.feature);
      selectedFeature = e.feature;
      btnRemove.disabled = false;
      map.fitBounds(bounds);
    }
  });
  google.maps.event.addListener(map.data, 'click', function (e) {
    if (e.hasOwnProperty("feature") === true) {
      selectedFeature = e.feature;
      btnRemove.disabled = false;
      if (e.feature.getGeometry().getType() === "Point") {
        map.setCenter(e.feature.getGeometry().get());
        map.setZoom(18);
      }
      showInfo(e);
    } else {
      selectedFeature = null;
      btnRemove.disabled = true;
    }
  });

  map.data.setStyle((feature) => {
    if (feature.getProperty("styles")) {
      featureStyleOptions = Object.assign(featureStyleOptions, JSON.parse(feature.getProperty("styles")));
      setFeatureStyleOptionControls();
    } else {
      feature.setProperty("styles", JSON.stringify(featureStyleOptions))
    }
    return featureStyleOptions;
  });

  addYourLocationButton();
  loadData();
  bindDataLayerListeners(map.data);
  strokeColorControl = document.getElementById('strokeColor');
  strokeOpacityControl = document.getElementById('strokeOpacity');
  strokeWeightControl = document.getElementById('strokeWeight');
  fillColorControl = document.getElementById('fillColor');
  fillOpacityControl = document.getElementById('fillOpacity');
  if (strokeColorControl !== null) {
    setFeatureStyleOptionControls();
    setStyleControlEvents();
  }
}

function setStyleControlEvents() {
  if (strokeColorControl !== null) {
    strokeColorControl.addEventListener('change', featureStyleOptionsControlChange);
    strokeOpacityControl.addEventListener('change', featureStyleOptionsControlChange);
    strokeWeightControl.addEventListener('change', featureStyleOptionsControlChange);
    fillColorControl.addEventListener('change', featureStyleOptionsControlChange);
    fillOpacityControl.addEventListener('change', featureStyleOptionsControlChange);
  }
}

function setFeatureStyleOptionControls() {
  if (strokeColorControl !== null) {
    strokeColorControl.value = featureStyleOptions.strokeColor;
    strokeOpacityControl.value = featureStyleOptions.strokeOpacity;
    strokeWeightControl.value = featureStyleOptions.strokeWeight;
    fillColorControl.value = featureStyleOptions.fillColor;
    fillOpacityControl.value = featureStyleOptions.fillOpacity;
  }
}

function featureStyleOptionsControlChange() {
  featureStyleOptions.strokeColor = strokeColorControl.value;
  featureStyleOptions.strokeOpacity = strokeOpacityControl.value;
  featureStyleOptions.strokeWeight = strokeWeightControl.value;
  featureStyleOptions.fillColor = fillColorControl.value;
  featureStyleOptions.fillOpacity = fillOpacityControl.value;
  // if (styleControls !== null)
  //   styleControls.value = JSON.stringify(featureStyleOptions);
  if (selectedFeature !== null) {
    selectedFeatureSetStyle(selectedFeature);
  }
}

function selectedFeatureSetStyle(f) {
  f.setProperty("styles", JSON.stringify(featureStyleOptions));
  map.data.revertStyle();
  map.data.overrideStyle(f, featureStyleOptions);
  saveData();
}

function loadData() {
  if (geom.value === "") return;
  let data = JSON.parse(geom.value);
  if (data !== undefined) {
    map.data.addGeoJson(data);
  }
  setControls();
}

function showInfo(event) {
  if (contents.length < 1) return;
  infoWindow.setPosition(event.latLng);
  let content = "";
  for (let key in contents) {
    let keys = contents[key];
    let value = key === "id" ? event.feature.getId() : event.feature.getProperty(key);
    value = value === undefined ? "" : value
    let cnt = keys[0] + ": " + value;
    if (keys.length > 1) {
      if (keys[1] === 'b') {
        cnt = "<b>" + cnt + "</b>"
      }
    }
    content += cnt + '<br>';
  }
  if (edit_url !== "" && event.feature.getId() !== undefined) {
    let url = edit_url.replace("{id}", selectedFeature.getId());
    content += '<a class="btn btn-info" href="{url}">Edit</a>'.replace("{url}", url);
  }
  infoWindow.setContent(content);
  infoWindow.open(map);
}

function bindDataLayerListeners(dataLayer) {
  dataLayer.addListener('addfeature', saveData);
  dataLayer.addListener('removefeature', saveData);
  dataLayer.addListener('setgeometry', saveData);
}

function extendBound(newbounds, feature) {
  if (feature === undefined) return newbounds;
  let featureType = feature.getGeometry().getType();
  if (featureType === 'LineString') {
    feature.getGeometry().getArray().forEach(function (latLng) {
      newbounds.extend(latLng);
    });
  } else if (featureType === 'Polygon') {
    feature.getGeometry().getArray().forEach(function (path) {
      path.getArray().forEach(function (latLng) {
        newbounds.extend(latLng);
      });
    });
  }
  return newbounds;
}

function getFeatureBounds() {
  let bounds = new google.maps.LatLngBounds();
  map.data.forEach(function (e) {
    bounds = extendBound(bounds, e);
  });
  return bounds;
}

function setControls() {
  let total = 0;
  let bounds = new google.maps.LatLngBounds();
  map.data.forEach(function (e) {
    total++;
    bounds = extendBound(bounds, e);
  });
  if (total > 0) {
    map.fitBounds(bounds);
    map.data.setDrawingMode(null);
    map.data.setControls(null);
    let zoomLevel = map.getZoom();
    if (total > 1) {
      map.data.forEach(function (e) {
        let bounds = new google.maps.LatLngBounds();
        bounds = extendBound(bounds, e);
        let properties = {};
        e.forEachProperty(
            function (val, key) {
              properties[key] = val;
            }
        );
        map.data.add({
          geometry: new google.maps.Data.Point(bounds.getCenter()),
          properties: properties,
          // id:e.getId()
        });
      });
    }
  } else {
    map.data.setControls(gmapControls);
    // map.data.setDrawingMode('polygon');
  }
}

function saveData() {
  map.data.toGeoJson(function (json) {
    geom.value = JSON.stringify(json);
  });
  setControls();
}

function addYourLocationButton() {
  let controlDiv = document.createElement('div');
  let btnCurrent = document.createElement('button');
  btnCurrent.type = "button";
  btnCurrent.style.backgroundColor = '#fff';
  btnCurrent.style.border = 'none';
  btnCurrent.style.outline = 'none';
  btnCurrent.style.width = '28px';
  btnCurrent.style.height = '28px';
  btnCurrent.style.borderRadius = '2px';
  btnCurrent.style.boxShadow = '0 1px 4px rgba(0,0,0,0.3)';
  btnCurrent.style.cursor = 'pointer';
  btnCurrent.style.marginRight = '10px';
  btnCurrent.style.padding = '0';
  btnCurrent.title = 'Your Location';
  controlDiv.appendChild(btnCurrent);

  let imgCurrent = document.createElement('div');
  imgCurrent.style.margin = '5px';
  imgCurrent.style.width = '18px';
  imgCurrent.style.height = '18px';
  imgCurrent.style.backgroundImage = 'url(https://maps.gstatic.com/tactile/mylocation/mylocation-sprite-2x.png)';
  imgCurrent.style.backgroundSize = '180px 18px';
  imgCurrent.style.backgroundPosition = '0 0';
  imgCurrent.style.backgroundRepeat = 'no-repeat';
  btnCurrent.appendChild(imgCurrent);
  let txtCurrent = document.createElement('i');
  txtCurrent.className = "fa";
  txtCurrent.ariaHidden = "true"; //<i class="fa fa-trash" aria-hidden="true"></i>
  imgCurrent.appendChild(txtCurrent);

  google.maps.event.addListener(map, 'center_changed', function () {
    imgCurrent.style['background-position'] = '0 0';
  });

  btnCurrent.addEventListener('click', function () {
    let imgX = 0,
        animationInterval = setInterval(function () {
          imgX = -imgX - 18;
          imgCurrent.style['background-position'] = imgX + 'px 0';
        }, 500);

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(function (position) {
        let latlng = new google.maps.LatLng(position.coords.latitude, position.coords.longitude);
        map.setCenter(latlng);
        map.setZoom(18);
        clearInterval(animationInterval);
        btnCurrent.style['background-position'] = '-144px 0';
      });
    } else {
      clearInterval(animationInterval);
      btnCurrent.style['background-position'] = '0 0';
    }
  });


  // let btnRemove = document.getElementById('btnRemove');
  btnRemove = document.createElement('button');
  btnRemove.type = "button";
  btnRemove.style.backgroundColor = '#fff';
  btnRemove.style.border = 'none';
  btnRemove.style.outline = 'none';
  btnRemove.style.width = '28px';
  btnRemove.style.height = '28px';
  btnRemove.style.borderRadius = '2px';
  btnRemove.style.boxShadow = '0 1px 4px rgba(0,0,0,0.3)';
  btnRemove.style.cursor = 'pointer';
  // btnRemove.style.marginRight = '10px';
  btnRemove.style.padding = '0';
  btnRemove.title = 'Delete Selected Feature';
  controlDiv.appendChild(btnRemove);
  let imgRemove = document.createElement('div');
  imgRemove.style.margin = '5px';
  imgRemove.style.width = '18px';
  imgRemove.style.height = '18px';
  btnRemove.appendChild(imgRemove);
  let txtRemove = document.createElement('i');
  txtRemove.className = "fa fa-trash";
  txtRemove.ariaHidden = "true"; //<i class="fa fa-trash" aria-hidden="true"></i>
  imgRemove.appendChild(txtRemove);

  btnRemove.addEventListener("click", function () {
    if (selectedFeature !== null) {
      map.data.remove(selectedFeature);
      selectedFeature = null;
      btnRemove.disabled = true;
      saveData();
      map.data.setControls(gmapControls);
    }
  });

  controlDiv.index = 1;
  map.controls[google.maps.ControlPosition.BOTTOM_CENTER].push(controlDiv);
}
