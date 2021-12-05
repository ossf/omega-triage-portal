$(document).ready(function () {
    /* Initialize Bootstrap Components */
    $('[data-toggle="popover"]').popover();
    $('[data-toggle="tooltip"]').tooltip();

    /* Add CSRF token to AJAX requests */
    $.ajaxSetup({
        'timeout': 15000,
        'beforeSend': function (jqXHR, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type) && !this.crossDomain) {
                jqXHR.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });

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
                    document.location.href = `/findings/${finding_uuid}`;
                    //window.open(`/findings/${finding_uuid}`, 'omega_findings');
                }
            });
        }
    });

    // Initialize the ACE editor
    initialize_editor();

    // Auto-open single-child nodes
    $("#data").on("open_node.jstree", function (e, data) {
        try {
            if (data.node.children.length == 1) {
                $('#data').jstree().open_node(data.node.children[0])
            }
        } catch (e) {
            console.log(`Error: ${e}`);
        }
    });
})

// General Purpose Helper Functions
let getCookie = function (name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const load_source_code = function (options) {
    $.ajax({
        'url': '/api/findings/get_source_code',
        'method': 'GET',
        'data': {
            'scan_uuid': options['scan_uuid'],
            'file_path': options['file_path']
        },
        'dataType': 'json',
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
            editor.resize();
            // Show the editor if needed
            $('#editor-container').removeClass('d-none');

            // Set the editor title
            $('#file_path').text(file_name);

            //var path_abbrev = path;
            //if (path_abbrev.length > 150) {
            //    path_abbrev = '...' + path_abbrev.substring(path_abbrev.length - 150, path_abbrev.length);
            //}
            //$('#editor-title .text').text(path_abbrev).attr('title', path);

            if (options['file-location'] != undefined) {
                let session = ace.edit('editor').getSession();
                session.clearAnnotations();
                session.setAnnotations([{
                    row: options['file-location'] - 1,
                    column: 0,
                    text: options['finding-title'],
                    type: 'error'
                }]);
            } else {
                ace.edit('editor').getSession().clearAnnotations();
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
        },
        'error': function (jqXHR, textStatus, errorThrown) {
            ace.edit('editor').getSession().clearAnnotations();
            ace.edit('editor').getSession().setMode('ace/mode/text')
            set_editor_text(`Error ${jqXHR.status}: ${jqXHR.responseJSON.message}.`);
        }
    });
};
const initialize_editor = function () {
    try {
        let editor = ace.edit("editor"),
            session = editor.getSession();
        editor.setOptions({
            useWorker: false
        });
        editor.setShowPrintMargin(false);
        editor.setTheme("ace/theme/cobalt");
        editor.setReadOnly(true)
        editor.setOptions({
            'fontFamily': 'Inconsolata',
            'fontSize': localStorage.getItem('last-used-editor-font-size') || '1.1rem',
        });
    } catch (e) {
        console.log(e);
    }
}

const set_editor_text = function (text) {
    let editor = ace.edit("editor");
    editor.getSession().setValue(text);
    editor.resize();
}

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

const beautify_source_code = () => {
    const beautify = ace.require("ace/ext/beautify");
    const editor = ace.edit("editor");
    if (!!beautify && !!editor) {
        beautify.beautify(editor.session);
    }
};

const toggle_word_wrap = () => {
    const session = ace.edit('editor').getSession();
    session.setUseWrapMode(!session.getUseWrapMode());
}

const change_font_size = (size) => {
    const editor = ace.edit('editor');
    let fontSize = editor.getFontSize();
    if (fontSize.indexOf('rem') > -1) {
        fontSize = fontSize.replace('rem', '');
        fontSize = parseFloat(fontSize) * size;
        fontSize = fontSize + 'rem';
    } else if (fontSize.indexOf('px') > -1) {
        fontSize = fontSize.replace('px', '');
        fontSize = parseFloat(fontSize) * size;
        fontSize = fontSize + 'px';
    }
    editor.setFontSize(fontSize);
    localStorage.setItem('last-used-editor-font-size', fontSize);
}