odoo.define('arabic_western_numerals_fix.fix_arabic_numbers', function(require) {
    "use strict";

    const core = require('web.core');
    const field_utils = require('web.field_utils');
    const luxon = require('luxon');

    const _t = core._t;

    const eastern = ['٠','١','٢','٣','٤','٥','٦','٧','٨','٩'];
    const western = ['0','1','2','3','4','5','6','7','8','9'];

    function convertArabicToWestern(str) {
        if (typeof str !== 'string') return str;
        return str.replace(/[٠-٩]/g, d => western[eastern.indexOf(d)]);
    }

    // Patch translations
    core._t = function (str) {
        return convertArabicToWestern(_t(str));
    };

    // Patch formatted datetime (Luxon output)
    const original_formatDate = field_utils.format.datetime;
    field_utils.format.datetime = function (value, options) {
        const res = original_formatDate(value, options);
        return convertArabicToWestern(res);
    };

    // Patch float/number formatting if needed
    const original_formatFloat = field_utils.format.float;
    field_utils.format.float = function (value, options) {
        const res = original_formatFloat(value, options);
        return convertArabicToWestern(res);
    };

});
