/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

'use strict';

$.fn.treestatus = function() {
    return this.each(function() {
        let $treestatus = $(this);

        // Register an on-click handler for each recent changes edit button.
        $('.recent-changes-edit').on("click", function () {
            // Get the `data-target` field for the edit button.
            let targetId = $(this).data('target');

            // Find the target element.
            let targetInput = $('#' + targetId);

            // Toggle the `disabled` property on the element.
            let isDisabled = targetInput.is(':disabled');
            targetInput.prop('disabled', !isDisabled);
        });

        // Register an on-click handler for each log update edit button.
        $('.log-update-edit').on("click", function () {
            // Get the `data-target` field for the edit button.
            let targetId = $(this).data('target');

            // Find the target element.
            let targetInput = $('#' + targetId);

            // Toggle the `disabled` property on the element.
            let isDisabled = targetInput.is(':disabled');
            targetInput.prop('disabled', !isDisabled);
        });

        // Toggle selected on all trees.
        $('.select-all-trees').on("click", function () {
            $('.tree-select-checkbox').prop('checked', true);
        });
    });
};
