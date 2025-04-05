/** Fix Arabic numerals to Western in Arabic UI (Odoo v18) **/
odoo.define('arabic_western_numerals_fix.fix_arabic_numbers', function(require) {
    "use strict";

    const core = require('web.core');
    const _t = core._t;

    const eastern = ['٠','١','٢','٣','٤','٥','٦','٧','٨','٩'];
    const western = ['0','1','2','3','4','5','6','7','8','9'];

    function convertArabicToWestern(str) {
        if (typeof str !== 'string') return str;
        return str.replace(/[٠-٩]/g, d => western[eastern.indexOf(d)]);
    }

    const patched_t = function(str) {
        return convertArabicToWestern(_t(str));
    };

    core._t = patched_t;
});
