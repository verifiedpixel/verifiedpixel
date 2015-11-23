'use strict';

angular.module('verifiedpixel.imagelist').directive('vpCommentText', [
    '$compile',
    function($compile) {
      return {
        scope : {comment : '='},
        link : function(scope, element, attrs) {

          var html;

          // replace new lines with paragraphs
          html = attrs.text.replace(/(?:\r\n|\r|\n)/g, '</p><p>');

          // map user mentions
          var mentioned = html.match(/\@([a-zA-Z0-9-_.]\w+)/g);
          _.each(mentioned, function(token) {
            var username = token.substring(1, token.length);
            if (scope.comment.mentioned_users &&
                scope.comment.mentioned_users[username]) {
              html = html.replace(
                  token, '<i sd-user-info data-user="' +
                             scope.comment.mentioned_users[username] +
                             '">' + token + '</i>');
            }
          });

          // build element
          element.html('<p><b>' + attrs.name + '</b> : ' + html +
                       '</p>');

          $compile(element.contents())(scope);
        }
      };
    }

]);
