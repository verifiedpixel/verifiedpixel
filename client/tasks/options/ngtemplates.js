'use strict';

module.exports = {
    app: {
        cwd: 'app',
        src: [
            'scripts/bower_components/superdesk/client/app/scripts/superdesk*/**/*.html',
            'scripts/verifiedpixel*/**/*.html',
        ],
        dest: 'app/scripts/vpp-templates.js',
        options: {
            htmlmin: {
                collapseWhitespace: true,
                collapseBooleanAttributes: true
            },
            bootstrap:  function(module, script) {
                return '"use strict";' +
                    'var vpptemplates = angular.module("vpp.templates", []);' +
                    'templates.run([\'$templateCache\', function($templateCache) {' +
                    script + ' }]);';
            }
        }
    }
};
