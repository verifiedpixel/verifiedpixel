define([], function() {
    'use strict';

    return function ImageToolsService() {

        /**
         * Reorient specified element.
         *
         * @param {number} orientation
         * @param {object} element
         * @returns {undefined}
         */
        this.reOrient = function reOrient(orientation, element) {
            // reset css first
            element.css({
                '-moz-transform': 'none',
                '-o-transform': 'none',
                '-webkit-transform': 'none',
                'transform': 'none',
                'filter': 'none',
                '-ms-filter': 'none'
            });
            switch (orientation) {
                case 1:
                    // No action needed
                    break;
                case 2:
                    element.css({
                        '-moz-transform': 'scaleX(-1)',
                        '-o-transform': 'scaleX(-1)',
                        '-webkit-transform': 'scaleX(-1)',
                        'transform': 'scaleX(-1)',
                        'filter': 'FlipH',
                        '-ms-filter': 'FlipH'
                    });
                    break;
                case 3:
                    element.css({
                        'transform': 'rotate(180deg)'
                    });
                    break;
                case 4:
                    element.css({
                        '-moz-transform': 'scaleX(-1)',
                        '-o-transform': 'scaleX(-1)',
                        '-webkit-transform': 'scaleX(-1)',
                        'transform': 'scaleX(-1) rotate(180deg)',
                        'filter': 'FlipH',
                        '-ms-filter': 'FlipH'
                    });
                    break;
                case 5:
                    element.css({
                        '-moz-transform': 'scaleX(-1)',
                        '-o-transform': 'scaleX(-1)',
                        '-webkit-transform': 'scaleX(-1)',
                        'transform': 'scaleX(-1) rotate(90deg)',
                        'filter': 'FlipH',
                        '-ms-filter': 'FlipH'
                    });
                    if (element.hasClass('vpp-selected-preview')) {
                        element.css({
                            'margin-top': '115px'
                        });
                    }
                    break;
                case 6:
                    element.css({
                        'transform': 'rotate(90deg)'
                    });
                    if (element.hasClass('vpp-selected-preview')) {
                        element.css({
                            'margin-top': '115px'
                        });
                    }
                    break;
                case 7:
                    element.css({
                        '-moz-transform': 'scaleX(-1)',
                        '-o-transform': 'scaleX(-1)',
                        '-webkit-transform': 'scaleX(-1)',
                        'transform': 'scaleX(-1) rotate(-90deg)',
                        'filter': 'FlipH',
                        '-ms-filter': 'FlipH'
                    });
                    if (element.hasClass('vpp-selected-preview')) {
                        element.css({
                            'margin-top': '115px'
                        });
                    }
                    break;
                case 8:
                    element.css({
                        'transform': 'rotate(-90deg)'
                    });
                    if (element.hasClass('vpp-selected-preview')) {
                        element.css({
                            'margin-top': '115px'
                        });
                    }
                    break;
            }
        }; // end reOrient

        /**
         * Functions for formatting EXIF data
         */
        function GPSArrayToFloat(input, ref){
            var d0 = input[0][0];
            var d1 = input[0][1];
            var d = (d0 / d1);

            var m0 = input[1][0];
            var m1 = input[1][1];
            var m = (m0 / m1);

            var s0 = input[2][0];
            var s1 = input[2][1];
            var s = (s0 / s1);
            var value = (d + (m / 60) + (s / 3600));

            if ((ref === 'S') || (ref === 'W')) {
                value = 0 - value;
            }
            return value;
        }

        this.convertExif = function convertExif(filemetaLowered, filemetaConverted) {
            var filemeta = (filemetaLowered) ? filemetaLowered : {};
            var converted = (filemetaConverted) ? filemetaConverted : {};
            // check to see if the file latitude record exists before
            // trying to return anything // longitude is there for the sake of completeness
            if (filemeta.gpsinfo){
                if (filemeta.gpsinfo.gpslatitude && filemeta.gpsinfo.gpslongitude) {
                    // lat is always first
                    converted.gpslat = GPSArrayToFloat(
                        filemeta.gpsinfo.gpslatitude,
                        filemeta.gpsinfo.gpslatituderef
                    );
                    converted.gpslon = GPSArrayToFloat(
                        filemeta.gpsinfo.gpslongitude,
                        filemeta.gpsinfo.gpslongituderef
                    );
                }
                if (filemeta.gpsinfo.gpsimgdirection) {
                    converted.gpsdirection = (
                        filemeta.gpsinfo.gpsimgdirection[0] /
                        filemeta.gpsinfo.gpsimgdirection[1]
                    ).toFixed(3);
                    converted.markerdirection = Math.ceil(converted.gpsdirection / 10) * 10;
                    if (filemeta.lensmodel && filemeta.lensmodel.match(/front/i)) {
                        converted.markerdirection = (converted.markerdirection + 180) % 360;
                    }
                    converted.gpsicon = {
                        url: '/images/gpsdirection/view-' + converted.markerdirection + '.png',
                        size: new google.maps.Size(100, 100),
                        origin: new google.maps.Point(0,0),
                        anchor: new google.maps.Point(50, 50)
                    };
                }
                if (filemeta.gpsinfo.gpsaltitude) {
                    converted.gpsaltitude = filemeta.gpsinfo.gpsaltitude[0] /
                        filemeta.gpsinfo.gpsaltitude[1];
                }
                if (filemeta.gpsinfo.gpsspeed) {
                    converted.gpsspeed = filemeta.gpsinfo.gpsspeed[0] /
                        filemeta.gpsinfo.gpsspeed[1];
                }
                if (filemeta.gpsinfo.gpstrack) {
                    converted.gpstrack = filemeta.gpsinfo.gpstrack[0] /
                        filemeta.gpsinfo.gpstrack[1];
                }
            }

            if (filemeta.aperturevalue) {
                converted.aperture = (
                    filemeta.aperturevalue[0] /
                    filemeta.aperturevalue[1]
                ).toFixed(1);
            }
            if (filemeta.exposuretime) {
                converted.exposuretime = (
                    filemeta.exposuretime[0] /
                    filemeta.exposuretime[1]
                ).toFixed(5);
            }
            if (filemeta.focallength) {
                converted.focallength = (
                    filemeta.focallength[0] /
                    filemeta.focallength[1]
                ).toFixed(2);
            }
            if (filemeta.exposuremode > -1) {
                switch(filemeta.exposuremode) {
                    case 0:
                        converted.exposuremode = 'Not defined';
                        break;
                    case 1:
                        converted.exposuremode = 'Manual';
                        break;
                    case 2:
                        converted.exposuremode = 'Normal program';
                        break;
                    case 3:
                        converted.exposuremode = 'Aperture priority';
                        break;
                    case 4:
                        converted.exposuremode = 'Shutter priority';
                        break;
                    case 5:
                        converted.exposuremode = 'Creative program';
                        break;
                    case 6:
                        converted.exposuremode = 'Action program';
                        break;
                    case 7:
                        converted.exposuremode = 'Portrait mode';
                        break;
                    case 8:
                        converted.exposuremode = 'Landscape mode';
                        break;
                }
            }

            if (filemeta.datetimeoriginal) {
                var dateTimeParts = filemeta.datetimeoriginal.split(' ');
                var dateParts = dateTimeParts[0].split(':');
                var year = dateParts[0];
                var month = dateParts[1];
                var day = dateParts[2];
                var timeParts = dateTimeParts[1].split(':');
                var hour = timeParts[0];
                var min = timeParts[1];
                var sec = timeParts[2];
                converted.datecaptured = new Date(year, month-1, day, hour, min, sec, 0);
            } else {
                converted.datecaptured = 'unknown';
            }

            return converted;
        };

    };
});
