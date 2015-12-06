var GeocodingPrecisionCalculator = function() {
    this.id = null;
    this.map = null;
};

GeocodingPrecisionCalculator.prototype.start = function() {
    var self = this;
    if (navigator.geolocation) {
        self.id = navigator.geolocation.watchPosition(
            function(position) {
                self._success(position);
            },
            self._error,
            {enableHighAccuracy:true, timeout:6000, maximumAge:600000}
        );
    }
}

GeocodingPrecisionCalculator.prototype._success = function(position) {
    var self = this;
    self.lat = position.coords.latitude;
    self.lng = position.coords.longitude;
    self.ll = {
        lat: self.lat,
        lng: self.lng
    };
    if(!self.me){
        self.me = new google.maps.Marker({
            position: self.ll,
            icon: '/static/image/gloc.png',
            map: self.map
        });
    }
    else{
        self.me.setPosition(self.ll);
    }
    self.map.panTo(self.ll);
}

GeocodingPrecisionCalculator.prototype.stop = function() {
    if (this.id) {
        navigator.geolocation.clearWatch(this.id);
    }
    this.id = null;
}

GeocodingPrecisionCalculator.prototype._error = function() {
    alert('位置情報取れない');
}

GeocodingPrecisionCalculator.prototype.initMap = function() {
    this.map = new google.maps.Map(document.getElementById('map'), {
        center: {
            lat: 35.681382,
            lng: 139.766084
        },
        zoom: 16
    });
    this.geocoder = new google.maps.Geocoder();
    this.start();
}
var gc = new GeocodingPrecisionCalculator();
