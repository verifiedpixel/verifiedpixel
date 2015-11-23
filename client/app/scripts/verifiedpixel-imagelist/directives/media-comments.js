'use strict';

angular.module('verifiedpixel.imagelist').directive('vpMediaComments', [
    'userList',
    'tagging',
    function(userList, tagging) {
      return {
        scope : {item : '='},
        templateUrl :
            'scripts/verifiedpixel-imagelist/views/comments-view.html',
        link : function(scope) {
          tagging.getTags(scope);
          scope.addTag = tagging.addTag;
          scope.removeTag = tagging.removeTag;
        }
      };
    }

]);
