'use strict';

angular.module('verifiedpixel.imagelist').filter('emailFilter', function() {
    return function(str) {
        return str ? str.replace(/^.*<(.*)>$/g, '\$1') : '';
    };
});
