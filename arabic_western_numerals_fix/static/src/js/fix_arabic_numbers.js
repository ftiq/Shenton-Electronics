/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { format } from "@web/core/utils/formatters";
import { patch } from "@web/core/utils/patch";

const eastern = ['٠','١','٢','٣','٤','٥','٦','٧','٨','٩'];
const western = ['0','1','2','3','4','5','6','7','8','9'];

function convertArabicToWestern(str) {
    if (typeof str !== 'string') return str;
    return str.replace(/[٠-٩]/g, d => western[eastern.indexOf(d)]);
}

// Patch translations (_t)
patch(_t, 'arabic_western_numerals_fix._t', (original) => {
    return (str, ...args) => {
        const translated = original(str, ...args);
        return convertArabicToWestern(translated);
    };
});

// Patch number/date formatter
patch(format, 'arabic_western_numerals_fix.format', (original) => {
    return (value, type, options) => {
        const result = original(value, type, options);
        return convertArabicToWestern(result);
    };
});
