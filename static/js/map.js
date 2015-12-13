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
            self._error, {
                enableHighAccuracy: true,
                timeout: 6000,
                maximumAge: 600000
            }
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
    self.geocoder.geocode({
        'location': self.ll
    }, function(results, status) {
        if (status === google.maps.GeocoderStatus.OK) {
            self.iw.setMap(null);
            self.map.setCenter(results[0].geometry.location);
            self.iw.setContent(results[0].formatted_address);
            self.iw.setPosition(results[0].geometry.location);
            self.iw.setMap(self.map);
            self.post(results[0]);
        } else {
            console.log('Geocode was not successful for the following reason: ' + status);
        }
    });
    if (!self.me) {
        self.me = new google.maps.Marker({
            position: self.ll,
            icon: '/static/image/gloc.png',
            map: self.map
        });
    } else {
        self.me.setPosition(self.ll);
    }
    self.map.panTo(self.ll);
}

GeocodingPrecisionCalculator.prototype.post = function(result) {
    var self = this;
    $.ajax({
        type: 'POST',
        url: '/api/post',
        data: {
            lat: self.lat,
            lng: self.lat,
            json: JSON.stringify(result)
        }
    }).done(function(){
        console.log('post');
    }).fail(function(){
        console.log('fail');
    })
}

GeocodingPrecisionCalculator.prototype.stop = function() {
    if (this.id) {
        navigator.geolocation.clearWatch(this.id);
    }
    this.id = null;
}

GeocodingPrecisionCalculator.prototype._error = function() {
    console.log('位置情報取れない');
}

GeocodingPrecisionCalculator.prototype.initMap = function() {
    this.map = new google.maps.Map(document.getElementById('map'), {
        center: {
            lat: 35.681382,
            lng: 139.766084
        },
        zoom: 16
    });
    this.iw = new google.maps.InfoWindow();
    this.geocoder = new google.maps.Geocoder();
    this.dm = new google.maps.DistanceMatrixService();
    this.start();
}
var gc = new GeocodingPrecisionCalculator();
