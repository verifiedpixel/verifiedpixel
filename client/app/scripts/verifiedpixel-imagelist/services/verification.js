'use strict';

angular.module('verifiedpixel.imagelist').service('verification', [
    'api',
    function(api) {
        this.refreshVerificationResults = function(item, provider) {
            api('manual_verification').save({
                'item_id': item._id, 'provider': provider
            });
        }
    }
])
