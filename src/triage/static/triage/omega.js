$(document).ready(function () {
    /*
     * Initialize the DataTable (finding list)
     */
    $('#finding_list').DataTable({
        select: {
            style: 'os',
            info: false
        },
        scrollResize: true,
        scrollCollapse: true,
        scrollY: '100',
        lengthChange: false,
        paging: false,
        info: false,
        searching: false,
        order: [
            [0, 'asc'],
            [1, 'asc']
        ],
        columnDefs: [
            { 'searchable': false, 'targets': [] },
        ],
        initComplete: function (settings, json) {
            $('#finding_list').on('select.dt', function (e, dt, type, indexes) {
                if (type === 'row' && indexes.length === 1) {
                    let row = $('#finding_list').DataTable().rows(indexes).nodes().to$();
                    let finding_uuid = row.data('finding-uuid');
                    window.open(`/findings/${finding_uuid}`, 'omega_findings');
                    //get_file_for_issue($('#finding_list').DataTable().rows(indexes).nodes().to$());
                }
            });
        }
    });
})
const load_source_code = function (options) {
    $.ajax({
        'url': '/api/findings/get_source_code',
        'method': 'GET',
        'data': {
            'finding-uuid': options['finding-uuid']
        },
        'success': function ({ file_contents, file_name }, textStatus, jqXHR) {
            let editor = ace.edit("editor");
            editor.getSession().setValue(atob(file_contents));
            let mode = ace.require("ace/ext/modelist").getModeForPath(file_name).mode;
            editor.session.setMode(mode);
            editor.setShowPrintMargin(false);
            editor.resize();

            // Show the editor if needed
            $('#editor-container').removeClass('d-none');

            //var path_abbrev = path;
            //if (path_abbrev.length > 150) {
            //    path_abbrev = '...' + path_abbrev.substring(path_abbrev.length - 150, path_abbrev.length);
            //}
            //$('#editor-title .text').text(path_abbrev).attr('title', path);

            if (options['file-location'] != '') {
                ace.edit('editor').getSession().setAnnotations([{
                    row: options['file-location'] - 1,
                    column: 0,
                    text: options['finding-title'],
                    type: 'error'
                }]);
            }

            // @TODO Are these necessary?
            //$('#package-source-external-link').data('package-url', $row.data('package-url'));
            //$('#issue-metadata-link').data('issue-id', $row.data('issue-id'));

            $(window).trigger('resize');
            $('#editor').css('height', $(window).height() - 395);

            //window.setTimeout(function() {
            //    ace.edit('editor').scrollToLine($row.data('line-number'), true, false);
            //    $('.bottom-row').css('opacity', 1.0);
            //}, 50);
        }
    });
};

const load_file_listing = function (options) {
    $.ajax({
        'url': '/api/findings/get_files',
        'method': 'GET',
        'data': options,
        'success': function (data, textStatus, jqXHR) {
            if ($('#data').jstree(true)) {
                $('#data').jstree(true).destroy();
            }
            let tree_data = data.data;
            $('#data').jstree({
                'core': {
                    'data': tree_data,
                    'multiple': false,
                    'themes': {
                        'dblclick_toggle': false,
                        'icons': true,
                        'name': 'proton',
                        'responsive': true
                    }
                },
                'plugins': ['sort']
            });
            $('#data').on({
                "loaded.jstree": function (event, data) {
                    $(this).jstree("open_all");
                },
                "changed.jstree": function (event, data) {
                    if (data.node.children.length === 0) {
                        load_source_code({
                            'package_url': data.node.li_attr.package_url,
                            'file_path': data.node.id
                        }, {
                            'finding_title': data.node.li_attr.finding_title,
                            'file_location': data.node.li_attr.finding_location
                        });
                    }
                }
            });
        }
    });
}

const load_blob_listing = function (options) {
    $.ajax({
        'url': '/api/findings/get_blob_list',
        'method': 'GET',
        'data': options,
        'success': function (data, textStatus, jqXHR) {
            if ($('#data_blob').jstree(true)) {
                $('#data_blob').jstree(true).destroy();
            }
            let tree_data = data.data;
            $('#data_blob').jstree({
                'core': {
                    'data': tree_data,
                    'multiple': false,
                    'themes': {
                        'dblclick_toggle': false,
                        'icons': true,
                        'name': 'proton',
                        'responsive': true
                    }
                },
                'plugins': ['sort']
            });
            $('#data_blob').on({
                "loaded.jstree": function (event, data) {
                    $(this).jstree("open_all");
                },
                "changed.jstree": function (event, data) {
                    if (data.node.children.length === 0) {
                        load_source_code({
                            'package_url': data.node.li_attr.package_url,
                            'file_path': data.node.id
                        });
                    }
                }
            });
        }
    });
}

const get_file_for_issue = function ($row) {
    load_source_code({
        'finding-uuid': $row.data('finding-uuid'),
        'finding-title': $row.data('finding-title'),
        'file-path': $row.data('file-path'),
        'file-location': $row.data('file-location'),
    });
    load_file_listing({ 'finding_uuid': $row.data('finding-uuid') });
    //load_blob_listing({ 'finding_uuid': finding_uuid });
}