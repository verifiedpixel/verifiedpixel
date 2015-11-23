'use strict';

angular.module('verifiedpixel.imagelist').directive('vpMediaTineye', [
    'userList',
    'verification',
    function(userList, verification) {
      return {
        scope : {item : '='},
        templateUrl :
            'scripts/verifiedpixel-imagelist/views/tineye-view.html',
        link : function(scope, elem) {
          scope.refreshVerificationResults = verification.refreshVerificationResults;
        }
      };
    }
]);
