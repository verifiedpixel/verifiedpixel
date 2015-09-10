'use strict';

describe('imagelist service', function() {
    'use strict';
    //beforeEach(module('templates'));
    beforeEach(module('verifiedpixel.imagelist'));
    //beforeEach(module('superdesk.search'));

    it('can create base query', inject(function(imagelist) {
        var query = imagelist.query();
        var criteria = query.getCriteria();
        var filters = criteria.query.filtered.filter.and;
        expect(filters).toContain({not: {term: {state: 'spiked'}}});
        expect(criteria.sort).toEqual([{versioncreated: 'desc'}]);
        expect(criteria.size).toBe(25);
    }));
/*
    it('can create query string query', inject(function($rootScope, imagelist) {
        var criteria = imagelist.query({q: 'test'}).getCriteria();
        expect(criteria.query.filtered.query.query_string.query).toBe('test');
    }));

    it('can set size', inject(function(imagelist) {
        var criteria = imagelist.query().size(10).getCriteria();
        expect(criteria.size).toBe(10);
    }));

    it('can sort items', inject(function(imagelist, $location, $rootScope) {
        imagelist.setSort('urgency');
        $rootScope.$digest();
        expect($location.search().sort).toBe('urgency:desc');
        expect(imagelist.getSort()).toEqual({label: 'News Value', field: 'urgency', dir: 'desc'});

        imagelist.toggleSortDir();
        $rootScope.$digest();
        expect(imagelist.getSort()).toEqual({label: 'News Value', field: 'urgency', dir: 'asc'});
    }));

    it('can be watched for changes', inject(function(imagelist, $rootScope) {
        var criteria = imagelist.query().getCriteria();
        expect(criteria).toEqual(imagelist.query().getCriteria());
        expect(criteria).not.toEqual(imagelist.query({q: 'test'}).getCriteria());
    }));

    describe('multi action bar directive', function() {

        var scope;

        beforeEach(module('superdesk.archive'));
        beforeEach(module('superdesk.authoring.multiedit'));
        beforeEach(module('superdesk.packaging'));

        beforeEach(inject(function($rootScope, $compile) {
            scope = $rootScope.$new();
            $compile('<div sd-multi-action-bar></div>')(scope);
            scope.$digest();
        }));

        it('can show how many items are selected', inject(function() {
            expect(scope.multi.count).toBe(0);

            scope.multi.toggle({_id: 1, selected: true});
            expect(scope.multi.count).toBe(1);

            scope.multi.reset();
            expect(scope.multi.count).toBe(0);
        }));

        it('can trigger multi editing', inject(function(multiEdit) {
            spyOn(multiEdit, 'create');
            spyOn(multiEdit, 'open');

            scope.multi.toggle({_id: 'foo', selected: true});
            scope.multi.toggle({_id: 'bar', selected: true});

            scope.action.multiedit();
            expect(multiEdit.create).toHaveBeenCalledWith(['foo', 'bar']);
            expect(multiEdit.open).toHaveBeenCalled();
        }));
    });
*/
});
