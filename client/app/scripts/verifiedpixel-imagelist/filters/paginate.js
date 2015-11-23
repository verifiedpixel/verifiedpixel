'use strict';


var objSlice = function (obj, start, end) {
    var sliced = {};
     var i = 0;
     for (var k in obj) {
         if (i >= start && i < end) {
            sliced[k] = obj[k];
          }
          i++;
     }

     return sliced;
};

angular.module('verifiedpixel.imagelist').filter('paginate', function() {
    return function(arr, pageNumber, pageSize) {
        pageNumber = pageNumber || 1;
        var end = pageNumber*pageSize,
            start = end-pageSize;
        if (arr.isArray) {
            return (arr || []).slice(start, end);
        } else {
            return objSlice(arr, start, end);
        }
    };
})
