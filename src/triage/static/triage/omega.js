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
            'scan_uuid': options['scan_uuid'],
            'file_path': options['file_path']
        },
        'success': function ({ file_contents, file_name, status }, textStatus, jqXHR) {
            let editor = ace.edit("editor");
            editor.getSession().setValue(atob(file_contents));
            var get_mode_filename = (file_name) => {
                if (file_name.indexOf('.sarif')) {
                    return `file_name${".json"}`
                }
                return file_name;
            }
            let mode = ace.require("ace/ext/modelist").getModeForPath(get_mode_filename(file_name)).mode;
            editor.session.setMode(mode);
            editor.setShowPrintMargin(false);
            editor.resize();
            editor.setTheme("ace/theme/cobalt");
            editor.setOptions({
                'fontFamily': 'Inconsolata',
                'fontSize': '14px',
            });

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
            $('#editor').css('height', $(window).height() - $('#editor').offset().top - 10);

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
                'animation': 40,
                'plugins': ['sort'],
                'sort': function (a, b) {
                    a1 = this.get_node(a);
                    b1 = this.get_node(b);
                    if (a1.children.length === 0 && b1.children.length === 0) {
                        return a1.text.localeCompare(b1.text);
                    } else if (a1.children.length === 0) {
                        return 1;
                    } else if (b1.children.length === 0) {
                        return -1;
                    } else {
                        return a1.text.localeCompare(b1.text);
                    }
                }
            });
            $('#data').on({
                "loaded.jstree": function (event, data) {
                    $(this).jstree("open_node", $(this).find('li:first'));
                },
                "changed.jstree": function (event, data) {
                    if (data.node.children.length === 0) {
                        const scan_uuid = $.data(document.body, 'current_finding').scan_uuid;
                        load_source_code({
                            'scan_uuid': scan_uuid,
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
}