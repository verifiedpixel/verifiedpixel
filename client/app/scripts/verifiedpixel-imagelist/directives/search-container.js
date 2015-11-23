'use strict';

angular.module('verifiedpixel.imagelist').directive('vpSearchContainer', [
    function() {
      return {
        controller : [
          '$scope',
          function SearchContainerController($scope) {
            this.flags = $scope.flags || {};
          }
        ]
      };
    }
]);
