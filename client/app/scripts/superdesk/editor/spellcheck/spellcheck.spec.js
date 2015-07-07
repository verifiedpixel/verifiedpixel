
'use strict';

describe('spellcheck', function() {
    var DICT = {
            what: 1,
            foo: 1,
            f1: 1,
            '3d': 1,
            is: 1,
            and: 1
        },
        USER_DICT = {
            content: {
                baz: 1
            }
        },
        TEXT = 'wha is foo, f1, 4k and 3d?',
        LANG = 'en',
        errors = [];

    beforeEach(module('superdesk.editor.spellcheck'));

    beforeEach(inject(function(dictionaries, spellcheck, $q) {
        spyOn(dictionaries, 'queryByLanguage').and.returnValue($q.when({_items: [
            {_id: 'foo', content: DICT},
            {_id: 'bar', content: {bar: 1}}
        ]}));
        spyOn(dictionaries, 'getUserDictionary').and.returnValue($q.when(USER_DICT));
        spellcheck.setLanguage(LANG);
    }));

    it('can spellcheck using global + user dictionaries', inject(function(spellcheck, dictionaries, $q, $rootScope) {
        spellcheck.errors('test what if foo bar baz').then(assignErrors);

        $rootScope.$digest();

        expect(errors).toEqual(['test', 'if']);
        expect(dictionaries.queryByLanguage).toHaveBeenCalledWith(LANG);
        expect(dictionaries.getUserDictionary).toHaveBeenCalledWith(LANG);
    }));

    it('can render errors in given node', inject(function(spellcheck, $rootScope) {
        var p = createParagraph(TEXT);

        spellcheck.render(p);
        $rootScope.$digest();

        expect(p.innerHTML)
            .toBe('<span class="sderror">wha</span> is foo, f1, <span class="sderror">4k</span> and 3d?');

        expect(spellcheck.clean(p)).toBe(TEXT);
    }));

    it('can render errors at the end of text', inject(function(spellcheck, $rootScope) {
        var p = createParagraph('what is buz');

        spellcheck.render(p);
        $rootScope.$digest();

        expect(p.innerHTML)
            .toBe('what is <span class="sderror">buz</span>');
    }));

    it('can remove errors and keep the marker', inject(function(spellcheck) {
        var p = createParagraph('what is <span class="sderror">b<span class="mark"></span>uz</span>');
        expect(spellcheck.clean(p)).toBe('what is b<span class="mark"></span>uz');
    }));

    it('can add words to user dictionary', inject(function(spellcheck, api, $rootScope) {
        spyOn(api, 'save');
        spellcheck.errors('test').then(assignErrors);
        $rootScope.$digest();
        expect(errors).toEqual(['test']);

        spellcheck.addWordToUserDictionary('test');

        spellcheck.errors('test').then(assignErrors);
        $rootScope.$digest();

        expect(errors).toEqual([]);
    }));

    it('can suggest', inject(function(spellcheck, api, $q) {
        spyOn(api, 'save').and.returnValue($q.when({}));
        spellcheck.suggest('test');
        expect(api.save).toHaveBeenCalledWith('spellcheck', {word: 'test', language_id: LANG});
    }));

    function assignErrors(_errors) {
        errors.splice(0, errors.length);
        errors.push.apply(errors, _errors);
    }

    function createParagraph(text) {
        var p = document.createElement('p');
        p.contentEditable = 'true';
        p.innerHTML = text;
        document.body.appendChild(p);
        return p;
    }

    describe('spellcheck menu', function() {
        it('can toggle auto spellcheck', inject(function(editor, $controller, $rootScope) {
            var ctrl = $controller('SpellcheckMenu');
            expect(ctrl.isAuto).toBe(true);

            var scope = $rootScope.$new(),
                settingsHandle = jasmine.createSpy('handle');

            scope.$on('editor:settings', settingsHandle);

            ctrl.pushSettings();
            expect(settingsHandle).toHaveBeenCalled();
            expect(editor.settings.spellcheck).toBe(true);

            ctrl.isAuto = false;
            ctrl.pushSettings();
            expect(editor.settings.spellcheck).toBe(false);

            var spellcheckHandle = jasmine.createSpy('handle');
            scope.$on('spellcheck:run', spellcheckHandle);
            ctrl.spellcheck();
            expect(spellcheckHandle).toHaveBeenCalled();
        }));
    });
});
