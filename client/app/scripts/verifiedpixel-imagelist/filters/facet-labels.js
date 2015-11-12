'use strict';

angular.module('verifiedpixel.imagelist').filter('facet-labels', function() {
    return function(input) {
        if (input.toUpperCase() === 'URGENCY') {
            return 'News Value';
        } else {
            return input;
        }
    };
})
