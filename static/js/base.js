var x = document.getElementById("demo");
step = 0
function getLocation() {
  
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(drawMap);
  } else {
    x.innerHTML = "Геолокация не поддерживается вашим броузером!";
  }
}

function sendLocation() {
  
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(drawMap);
  } else {
    x.innerHTML = "Геолокация не поддерживается вашим броузером!";
  }
}

getLocation()
function showPosition(position) {
  x.innerHTML = "Latitude: " + position.coords.latitude +
  "<br>Longitude: " + position.coords.longitude;
}
function drawMap(position){
  x.innerHTML = "Latitude: " + position.coords.latitude +
  "<br>Longitude: " + position.coords.longitude;
mymap = L.map('mapid').setView([position.coords.latitude, position.coords.longitude], 9);
marker = L.marker(mymap.getCenter()).addTo(mymap)
marker.bindPopup("<b>Hello world!</b><br>I am a popup.").openPopup();

L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
	maxZoom: 18,
	attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, ' +
		'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
	id: 'mapbox/streets-v11',
	tileSize: 512,
	zoomOffset: -1
}).addTo(mymap);
}

// $("button").click(function(){
//   $.post("demo_test_post.asp",
//   {
//     name: "Donald Duck",
//     city: "Duckburg"
//   },
//   function(data, status){
//     alert("Data: " + data + "\nStatus: " + status);
//   });
// });


var currPosition;
navigator.geolocation.getCurrentPosition(function(position) {
    updatePosition(position);
    setInterval(function(){
        var lat = currPosition.coords.latitude;
        var lng = currPosition.coords.longitude;
        jQuery.ajax({
            type: "POST", 
            url:  "./user/location", 
            data: 'x='+lat+'&y='+lng, 
            cache: false
        });
    }, 1000);
}, errorCallback); 

var watchID = navigator.geolocation.watchPosition(function(position) {
    updatePosition(position);
});

function updatePosition( position ){
    currPosition = position;
	// var marker = L.marker([currPosition.coords.latitude+step, currPosition.coords.longitude+step]).addTo(mymap);
	marker.setLatLng([currPosition.coords.latitude+step, currPosition.coords.longitude+step]).update();
	// marker.bindPopup("<b>Hello world!</b><br>I am a popup.").openPopup();
	step += 0.001

}

function errorCallback(error) {
    var msg = "Can't get your location. Error = ";
    if (error.code == 1)
        msg += "PERMISSION_DENIED";
    else if (error.code == 2)
        msg += "POSITION_UNAVAILABLE";
    else if (error.code == 3)
        msg += "TIMEOUT";
    msg += ", msg = "+error.message;

    alert(msg);
}

