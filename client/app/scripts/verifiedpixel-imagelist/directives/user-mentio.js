'use strict';

angular.module('verifiedpixel.imagelist').directive('vpUserMentio', [
    'userList',
    function(userList) {
      return {
        templateUrl :
            'scripts/verifiedpixel-imagelist/views/mentions.html',
        link : function(scope, elem) {
          scope.users = [];

          // filter user by given prefix
          scope.searchUsers = function(prefix) {
            return userList.get(prefix, 1, 10)
                .then(function(result) {
                  scope.users = _.sortBy(result._items, 'username');
                });

          };

          scope.selectUser = function(user) {
            return '@' + user.username;
          };

          scope.$watchCollection(
              function() { return $('.users-list-embed>li.active'); },
              function(newValue) {
                if (newValue.hasClass('active')) {
                  $('.mentio-menu').scrollTop(newValue.position().top);
                }
              });
        }
      };
    }
]);
