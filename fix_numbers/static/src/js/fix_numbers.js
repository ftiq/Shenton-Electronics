odoo.define('fix_numbers.force_english_numbers', function (require) {
    "use strict";

    var session = require('web.session');

    if (session.user_context.lang && session.user_context.lang.startsWith('ar')) {
        Number.prototype.toLocaleString = function() {
            return this.toString();
        };
    }
});
