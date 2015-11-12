'use strict';

module.exports = {
    app: {
        cwd: 'app',
        src: [
            //'scripts/bower_components/superdesk/client/app/scripts/superdesk*/**/*.html',
            'scripts/verifiedpixel*/**/*.html'
        ],
        dest: 'app/scripts/templates-cache.js',
        options: {
            htmlmin: {
                collapseWhitespace: true,
                collapseBooleanAttributes: true
            },
            bootstrap:  function(module, script) {
                return '"use strict";' +
                    'angular.module("verifiedpixel.templates-cache", [])' +
                    '.run([\'$templateCache\', function($templateCache) {' +
                    script + ' }]);';
            }
        }
    }
};
