from xml.etree.ElementTree import Element, tostring
from xml.dom import minidom
import datetime
import collections
import os
import sys
import re
import urllib
import time

RESULT_COLORS = {"passed": "resultpass",
                 "failed": "resultfail",
                 "info": "resultblocked",
                 "section": "resultskipped"}
RESULT_TYPES = ['PASSED',
               'FAILED',
               'BLOCKED',
               'SKIPPED',
               'INFO']
replacement_logs = []

JS_DIR_DEFAULT = "/static/js/common"
CSS_DIR_DEFAULT = "/static/css/common"

NG_APP_NAME = "FUN_XML"

def get_timestamp_string():
    current_time = datetime.datetime.now()
    now = str(current_time.hour) + "_" + str(current_time.minute) + "_" + str(current_time.second) + str(
        current_time.microsecond)
    return str(now)


def get_xml_string(xml):
    s = ""
    try:
        s = minidom.parseString(tostring(xml)).toprettyxml(indent=' ')
    except Exception as ex:
        print("ERROR: unable to xmlize: {}".format(xml))
        s = "ERROR"
    return s

class GenericTable:
    def __init__(self, id, headers, rows_list=None):
        table = GenericElement("table", id=id)
        header_row = GenericElement("tr")
        for header in headers:
            th = GenericElement("th")
            th.text = header
            header_row.append(th)
        table.append(header_row)
        self.table = table
        if rows_list:
            for row in rows_list:
                self.add_row(row=row)

    def add_row(self, row):
        one_row = GenericElement("tr")
        for data in row:
            td = GenericElement("td")
            td.text = str(data)
            one_row.append(td)
        self.table.append(one_row)




class GenericElement(Element):
    def __init__(self,
                 tag,
                 id=None,
                 class_name=None):
        super(GenericElement, self).__init__(tag)
        if id:
            self.set_attribute(attribute="id", attribute_value=id)
        if class_name:
            self.set_attribute(attribute="class", attribute_value=class_name)

    def set_attribute(self, attribute, attribute_value):
        self.set(attribute, attribute_value)


class _XmlHead(Element):
    def __init__(self, use_boiler_plate=True):
        super(_XmlHead, self).__init__("head")
        if use_boiler_plate:
            self.do_boiler_plate()

    def __repr__(self):
        return self.get()

    def do_boiler_plate(self):

        # Add Scripts

        self.add_script(src="https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js")
        self.add_script(src="{}/bootstrap.min.js".format(JS_DIR_DEFAULT))
        self.add_script(src="{}/jsoneditor.js".format(JS_DIR_DEFAULT))
        self.add_script(src="http://code.highcharts.com/highcharts.js")
        self.add_script(src="http://code.highcharts.com/modules/exporting.js")

        self.add_script(src="{}/script_result.js".format(JS_DIR_DEFAULT))

        # Add Links
        self.add_link(href="{}/bootstrap.min.css".format(CSS_DIR_DEFAULT), rel="stylesheet")
        self.add_link(href="{}/jsoneditor.css".format(CSS_DIR_DEFAULT), rel="stylesheet")
        self.add_link(href="https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css", rel="stylesheet")
        self.add_link(href="{}/script_result.css".format(CSS_DIR_DEFAULT), rel="stylesheet")
        self.add_link(href="https://cdnjs.cloudflare.com/ajax/libs/jasny-bootstrap/3.1.3/css/jasny-bootstrap.min.css", rel="stylesheet")

    def add_link(self, href, rel):
        element = GenericElement("link")
        element.set("href", href)
        element.set("rel", rel)
        self.append(element)

    def add_script(self, src, type="text/javascript"):
        element = GenericElement("script")
        element.set("type", type)
        element.set("src", src)
        element.text = " "
        self.append(element)

    def add_local_script(self, local_script):
        element = GenericElement("script")
        element.text = local_script
        self.append(element)

    def add_local_style(self, local_style):
        element = GenericElement("style")
        element.text = local_style
        self.append(element)


class TopologyPageContent:
    def __init__(self):
        self.tree = GenericElement("div", id="topology", class_name="tab-pane")
        self.tree.text = "Topology"

    def get(self):
        return self.tree

    def set_topology_json_filename(self, filename):
        json_editor = GenericElement("div", id="topology-json")
        json_editor.set_attribute(attribute="data-path", attribute_value=filename)
        json_editor.text = " "
        self.tree.append(json_editor)

class AuxPageContent:
    def __init__(self):
        self.tree = GenericElement("div", id="aux", class_name="tab-pane")
        self.ul = GenericElement("ul")
        self.ul.text = " "
        self.tree.text = ""
        self.tree.append(self.ul)

    def get(self):
        return self.tree

    def add_file(self, description, filename):
        li = GenericElement("li")
        a = GenericElement("a")
        a.set_attribute("href", filename)
        a.set_attribute("target", "_blank")
        a.text = description
        li.append(a)
        self.ul.append(li)

class ScriptContent:
    def __init__(self):
        self.tree = GenericElement("div", id="script", class_name="tab-pane")
        self.tree.text = " "
        fetch_script_button = GenericElement("button", id="fetch-script-button", class_name="btn btn-primary")
        fetch_script_button.text = "Fetch Script"

        code_section = GenericElement("pre", id="code-section")
        code_section.text = "Please click Fetch Script"
        self.tree.append(fetch_script_button)
        self.tree.append(code_section)

    def get(self):
        return self.tree


class DocumentationContent:
    def __init__(self, full_script_path):
        logs_table = GenericTable(id="documentation-logs-table", headers=["Logs"])
        logs_table.table.set_attribute("style", "display: none")

        headers = ["Id", "Summary", "Steps"]
        self.tree = GenericElement("div", id="documentation", class_name="tab-pane")
        self.tree.set("role", "tabpanel")
        self.tree.set_attribute("full-script-path", full_script_path)

        spinner_div = GenericElement("div", id="spinner", class_name="loader")
        spinner_div.text = " "

        fluid_div = GenericElement("div", id="documentation-fluid-div")

        self.generic_table = GenericTable(id="documentation-table", headers=headers, rows_list=None)
        table = self.generic_table.table
        table.set_attribute(attribute="width", attribute_value="7%")
        table.set_attribute(attribute="class", attribute_value="table table-nonfluid table-bordered")

        # publish_button = GenericElement("button", id="test-case-publish-button", class_name="btn btn-labeled btn-success")
        # span = GenericElement("span", class_name="btn-label")
        # i = GenericElement("i", class_name="glyphicon glyphicon-upload")
        # i.text = " "
        # span.append(i)
        # publish_button.append(i)
        # publish_button.text = "Publish"
        # fluid_div.append(publish_button)

        fluid_div.append(table)

        alert_div = GenericElement("div", id="alert_placeholder")
        alert_div.text = " "

        progress_bar_container = GenericElement("div", id="progress-bar-container")
        progress_bar_container.set_attribute("style", "display: none")
        progress_bar_label = GenericElement("label", class_name="label label-default")
        progress_bar_label.set_attribute("for", "publish-progress-bar-div")
        progress_bar_label.text = "Progress"
        progress_bar_div = GenericElement("div", id="publish-progress-bar-div")
        progress_bar = GenericElement("div", id="publish-progress-bar")
        progress_bar.text = " "
        progress_bar_div.append(progress_bar)
        progress_bar_div.text = " "
        progress_bar_container.append(progress_bar_label)
        progress_bar_container.append(progress_bar_div)
        progress_bar_container.append(spinner_div)
        self.tree.append(progress_bar_container)

        # test_button = GenericElement("button", id="test-button")
        # test_button.text = "Test"

        self.tree.append(alert_div)
        self.tree.append(logs_table.table)
        # self.tree.append(test_button)
        self.tree.append(fluid_div)
        self.tree.text = " "

    def get(self):
        return self.tree

    def add(self, id, summary, steps):
        steps = steps.strip().replace("\n", "<br>")

        row = [str(id), summary, steps]
        self.generic_table.add_row(row)


class PageContent:
    def __init__(self, summary_chart=True, enable_bugs=True, variants=None):
        self.summary_chart = summary_chart
        self.enable_bugs = enable_bugs
        self.variants = variants
        self.messages = []

        self.tree = GenericElement("div", id="wrapper", class_name="tab-pane active")
        self.tree.set("role", "tabpanel")
        self.side_wrapper = GenericElement("div", id="sidebar-wrapper")
        # self.tree.append(self.get_header_nav())
        self.tree.append(self.side_wrapper)
        self.add_side_wrapper_table()
        self.page_content_wrapper = self.get_page_content_wrapper()
        self.tree.append(self.page_content_wrapper)

        self.results = collections.OrderedDict()
        for r in RESULT_TYPES:
            self.results[r] = 0

    def get_header_nav(self):
        header_nav = GenericElement("nav") # navbar navbar-fixed-top")
        header_nav.set("style", "top: 60px")

        header_nav.set("role", "navigation")
        header_nav_div = GenericElement("div") # , class_name="navbar-header")
        header_nav.append(header_nav_div)

        # list_element = GenericElement("li", class_name="sidebar-brand")
        # smenu_anchor = GenericElement("button",
        #                             id="summary_toggle",
        #                             class_name="btn btn-default")
        # glyph_button = GenericElement("span", id="summary_collapse", class_name="glyphicon glyphicon-arrow-left")
        # glyph_button.text = ''
        # menu_anchor.append(glyph_button)
        # header_nav.append(menu_anchor)

        # anchor = GenericElement("button", class_name="btn btn-default", id="test_suite")
        # anchor.text = "Script Name" # self.script_name
        # anchor.set("href", "#")
        # header_nav.append(anchor)
        return header_nav

    def add_side_wrapper_table(self):
        filter_input = GenericElement("input", id="test_case_summary_filter", class_name="form-control")
        filter_input.set("placeholder", "Type Here to filter test cases...")
        self.side_wrapper.append(self.get_header_nav())
        # self.side_wrapper.append(filter_input)

        side_wrapper_table = GenericElement("table", id="side_wrapper_table", class_name="table table-nonfluid")
        side_wrapper_table.text = " "
        self.side_wrapper.append(side_wrapper_table)

        one_row = GenericElement("tr")
        column_names = ['Id', 'Result', 'Testcase']
        if self.variants:
            column_names.extend(self.variants)

        for column_name in column_names:
            one_header = GenericElement("th")
            one_header.text = column_name
            one_row.append(one_header)
        side_wrapper_table.append(one_row)
        self.side_wrapper_table = side_wrapper_table

    def start_test(self, id, summary, href, result, bugs=None, variants=None):
        if not result.lower() == "ignored":
            if result.lower() in self.results:
                self.results[result.lower()] += 1
        else:
            return
        one_row = GenericElement("tr", class_name="test_case_summary_row")

        one_table_data = GenericElement("td")
        one_table_data.text = str(id)
        one_row.append(one_table_data)

        one_table_data = GenericElement("td")
        result_anchor = GenericElement("a", class_name=" test_case_summary")
        result_anchor.set("href", href)
        result_span = GenericElement("span")
        result_span.text = result
        if result.lower() in RESULT_COLORS:
            result_span.set_attribute(attribute="class", attribute_value=RESULT_COLORS[result.lower()])
        result_anchor.append(result_span)
        one_table_data.append(result_anchor)
        one_row.append(one_table_data)

        one_table_data = GenericElement("td")
        one_table_data.text = summary
        one_row.append(one_table_data)

        one_table_data = GenericElement("td")
        result_anchor = GenericElement("a")
        result_anchor.set("href", href)
        result_span = GenericElement("span")
        result_span.text = "pass"
        result_span.set_attribute(attribute="class", attribute_value=RESULT_COLORS["passed".lower()])
        result_anchor.append(result_span)
        one_table_data.append(result_anchor)
        # .append(one_table_data)

        if self.enable_bugs and False:
            one_table_data = GenericElement("td")
            if bugs:
                for i in bugs:
                    bug_anchor = GenericElement("a")
                    m = re.search(r'(\S+)', str(i))
                    bug_id = 0
                    if m:
                        bug_id = m.group(1)
                    bug_anchor.set("href", "https://fungible.jira.local/browse/" + str(bug_id))
                    bug_anchor.text = str(i)
                    one_table_data.append(bug_anchor)
            else:
                one_table_data.append(GenericElement("div"))
            one_row.append(one_table_data)

        self.side_wrapper_table.append(one_row)

    def finalize(self):
        pass

    def get_summary_distribution_string(self):
        s = ""
        for r in RESULT_TYPES:
            s += "['" + r + "'," + str(self.results[r] * 100/len(RESULT_TYPES)) + "],"
        s = s.strip(",")
        return s

    def get_page_content_wrapper(self):
        page_content_wrapper = GenericElement("div", id="page_content_wrapper", class_name="container-fluid")
        page_content_wrapper.text = ""
        # container_fluid_class = GenericElement("div", class_name="container-fluid")
        # row_class = GenericElement("div", class_name="row")
        # container_fluid_class.append(row_class)
        # self.page_content_wrapper.append(container_fluid_class)
        # self.tree.append(self.page_content_wrapper)
        self.panel_group = self.get_panel_group()

        # self.panel_group.append(self.messages_panel)

        page_content_wrapper.append(self.panel_group)
        return page_content_wrapper

    def get_messages_panel(self):
        panel = GenericElement("div", class_name="messages-div")
        self.messages_panel = GenericElement("ul", id="messages")
        panel.append(self.messages_panel)
        return panel

    def add_message(self, message):
        self.messages.append(message)
        message_div = GenericElement("li")
        message_div.text = message
        self.messages_panel.append(message_div)

    def get_panel_group(self):
        panel_group = GenericElement("div", id="panel-group")
        panel_anchor = GenericElement("button", id="summary_toggle", class_name="btn btn-default")
        glyph_button = GenericElement("span", id="summary_collapse", class_name="fa fa-caret-square-o-left")
        glyph_button.text = ''
        panel_anchor.append(glyph_button)
        # self.messages_panel = self.get_messages_panel()
        # panel_group.append(self.messages_panel)
        panel_group.append(panel_anchor)
        # self.tree.append(self.panel_group)
        return panel_group

    def add_panel(self, panel):
        self.panel_group.append(panel)

    def pretty_print(self):
        print(minidom.parseString(tostring(self.tree)).toprettyxml(indent=' '))

    def get(self):
        return self.tree


class TestSection(GenericElement):
    def __init__(self, id, summary, page_content, enable_long_summary=True,
                 enable_checkpoint_table=True,
                 log_directory=os.path.dirname(os.path.realpath(sys.argv[0]))):
        self.set_href_id(id=id, summary=summary)
        super(TestSection, self).__init__("div", class_name="panel panel-default", id=self.get_href_id() + "_top")

        # Settings
        self.enable_long_summary = enable_long_summary
        self.id = id
        self.summary = summary
        self.log_directory = log_directory
        self.log_filename = None
        self.page_content = page_content
        self.saved_log = ""
        self.bugs = []
        self.checkpoint_table = None
        self.one_checkpoint = None
        self.enable_checkpoint_table = enable_checkpoint_table
        self.addendums = {}

        #  Actions

        self.panel_heading = self.get_panel_heading(summary=summary)
        # self.body = GenericElement("div", class_name = "panel-collapse collapse in", id = self.get_href_id())
        self.body = GenericElement("div", class_name="accordion-body collapse", id=self.get_href_id())
        self.long_summary_button = self.get_long_summary_button()
        self.long_summary = self.get_long_summary()
        self.checkpoint_table = self.get_checkpoint_table()
        self.test_log = self.get_test_log(log="Test Log:\n")

        # Construct div
        self.body.append(self.test_log)
        self.append(self.panel_heading)
        if self.enable_long_summary and (self.id not in ["-", "*"]):
            self.append(self.long_summary_button)
            self.append(self.long_summary)

        if self.enable_checkpoint_table and (self.id not in ["-", "*"]):
            # self.append(self.filter_input)
            self.append(self.checkpoint_table)
        self.append(self.body)

    def add_addendum(self, header, text=None):
        if not header in self.addendums:
            addendum_heading = GenericElement("div", class_name="panel-heading")

            # anchor
            addendum_heading_anchor = GenericElement("a", class_name="accordion-toggle collapsed")
            addendum_heading_anchor.set("data-toggle", "collapse")
            addendum_heading_anchor.set("data-parent", "#accordion")
            ts = get_timestamp_string() + "addendum"
            addendum_heading_anchor.set("href", "#" + ts)

            addendum_heading.append(addendum_heading_anchor)
            addendum_heading_anchor.text = header
            self.append(addendum_heading)

            addendum = GenericElement("div", class_name="accordion-body collapse", id=ts)
            if text:
                addendum.text = "<pre>" + text + "</pre>"
            self.append(addendum)
            self.addendums[header] = {"addendum": addendum}

        return self.addendums[header]["addendum"]

    def _add_tab_panel(self, header):
        if not "tab_panel" in self.addendums[header]:
            tab_panel = GenericElement("div")
            tab_panel.set("role", "tab_panel")
            self.addendums[header]["tab_panel"] = tab_panel
            self.addendums[header]["addendum"].append(tab_panel)
        return self.addendums[header]["tab_panel"]

    def _add_panel_items(self, tab_panel, panel_items):
        ul = GenericElement("ul", class_name="nav nav-tabs")
        ul.set("role", "tab_list")
        time.sleep(0.001)
        ts = get_timestamp_string()
        href_dict = {}
        index = 0
        panel_items.update({"Memory": ""})
        for k in panel_items:
            li = GenericElement("li")
            # li.set("role", "presentation")
            anchor = GenericElement("a")
            anchor.set("role", "tab")
            if index == 0:
                li.set_attribute(attribute="class", attribute_value="active")

            href = ts # + k.replace(" ", "_")
            href = urllib.quote(href)
            href_dict[k] = href
            anchor.set("href", "#" + href)
            anchor.set("aria-controls", str(index))
            anchor.set("data-toggle", "tab")
            anchor.text = k
            li.append(anchor)
            ul.append(li)
            index += 1
        tab_panel.append(ul)

        tab_content = GenericElement("div", class_name="tab-content")
        index = 0
        for k in panel_items:

            tab_pane = GenericElement("div", id=href_dict[k])
            tab_pane.set("role", "tabpanel")
            if index == 0:
                tab_pane.set("class", "tab-pane active")
                index += 1
            else:
                tab_pane.set("class","tab-pane")
            if k == "Memory":
                memory_chart = GenericElement("div", id="memory_chart")
                memory_chart.text = "."
                tab_pane.append(memory_chart)
            else:
                pre = GenericElement("pre")
                pre.text = panel_items[k]
                tab_pane.append(pre)
            tab_content.append(tab_pane)

        tab_panel.append(tab_content)
        return tab_panel


    def _add_table_panel_items(self, header, panel_items):
        addendum = self.addendums[header]
        tab_panel = addendum["tab_panel"]
        if not "ul" in addendum:
            ul = GenericElement("ul", class_name="nav nav-tabs")
            ul.set("role", "tab_list")
            addendum["ul"] = ul
            addendum["li_count"] = 0
            tab_panel.append(ul)
        ul = addendum["ul"]
        ts = get_timestamp_string()
        href_dict = {}
        for k in panel_items:
            time.sleep(0.001)
            li = GenericElement("li")
            li.set("role", "presentation")
            anchor = GenericElement("a")
            anchor.set("role", "tab")
            if not addendum["li_count"]:
                li.set_attribute(attribute="class", attribute_value="active")
            href = ts # + k.replace(" ", "_")
            href_dict[k] = href
            anchor.set("href", "#" + href)
            anchor.set("aria-controls", "profile")
            anchor.set("data-toggle", "tab")
            anchor.text = k
            li.append(anchor)
            ul.append(li)
            addendum["li_count"] += 1

        if not "tab_content" in addendum:
            tab_content = GenericElement("div", class_name="tab-content")
            addendum["tab_content"] = tab_content
            tab_panel.append(tab_content)

        tab_content = addendum["tab_content"]
        for k in panel_items:
            tab_pane = GenericElement("div", id=href_dict[k])
            tab_pane.set("role", "tab_panel")
            if addendum["li_count"] == 1:
                tab_pane.set("class", "tab-pane active")
            else:
                tab_pane.set("class", "tab-pane")

            table = GenericTable(id="unknown",
                                 headers=panel_items[k]["headers"],
                                 rows_list=panel_items[k]["rows"]).table

            table.set_attribute(attribute="width", attribute_value="7%")
            table.set_attribute(attribute="class", attribute_value="table table-nonfluid table-bordered")

            tab_pane.append(table)
            tab_content.append(tab_pane)

        # tab_panel.append(tab_content)
        return tab_panel

    def get_table(self, headers, rows_list):
        table = GenericElement("table")
        table.set_attribute(attribute="width", attribute_value="7%")
        table.set_attribute(attribute="class", attribute_value="table table-nonfluid table-bordered")
        header_row = GenericElement("tr")
        for header in headers:
            th = GenericElement("th")
            th.text = header
            header_row.append(th)
        table.append(header_row)
        for row in rows_list:
            one_row = GenericElement("tr")
            for data in row:
                td = GenericElement("td")
                td.text = data
                one_row.append(td)
            table.append(one_row)

        return table


    def add_collapsible_tab_panel(self, header, panel_items):
        self.add_addendum(header=header)
        tab_panel = self._add_tab_panel(header=header)
        self._add_panel_items(tab_panel=tab_panel, panel_items=panel_items)

    def add_collapsible_tab_panel_tables(self, header, panel_items):
        self.add_addendum(header=header)
        tab_panel = self._add_tab_panel(header=header)
        self._add_table_panel_items(header=header, panel_items=panel_items)

    def set_href_id(self, id, summary):
        self.href_id = get_timestamp_string()

    def get_href_id(self):
        return self.href_id

    def get_summary(self):
        return self.summary

    def get_long_summary_button(self, long_summary=""):
        show_long_summary_button = GenericElement("a",
                                                      class_name="long_summary_button",
                                                      id=self.get_href_id() + "long_summary_button")
        show_long_summary_button.text = "&nbsp;Steps"
        return show_long_summary_button

    def get_long_summary(self, long_summary=""):
        long_summary = GenericElement("div", class_name='preformatted', id=self.get_href_id() + "long_summary")
        long_summary.text = "\n" + "Long Description: Not Available"
        long_summary.set("style", "display:none")
        return long_summary

    def set_long_summary(self, long_summary):
        self.long_summary.text = "\n" + long_summary

    def set_bugs(self, bugs):
        self.bugs = bugs

    def append_long_summary(self, s):
        self.long_summary.text = self.long_summary.text + "\n" + s

    def get_id(self):
        return self.id

    def get_panel_heading(self, summary):
        heading = GenericElement("h5", class_name="panel-heading")

        # anchor
        self.heading_anchor = GenericElement("a", class_name="accordion-toggle collapsed")
        self.heading_anchor.set("data-toggle", "collapse")
        self.heading_anchor.set("data-parent", "#accordion")
        self.heading_anchor.set("href", "#" + self.get_href_id())

        # self.test_section_result = GenericElement("span")
        self.test_section_result = GenericElement("span")

        #self.heading_anchor.append(self.test_section_result)
        heading.append(self.test_section_result)
        self.test_section_result.text = "\n"
        heading.append(self.heading_anchor)
        self.heading_anchor.text = summary

        return heading

    def end_test(self, result, bugs=[]):

        if not self.one_checkpoint:
            self.checkpoint_table.set_attribute("style", "display:none")

        self.test_section_result.text = "\n"
        if result.lower() in RESULT_COLORS:
            if "pass" in result.lower():
                self.test_section_result.set_attribute(attribute="class", attribute_value="{}".format("glyphicon glyphicon-ok"))
                self.test_section_result.set_attribute(attribute="style", attribute_value="color:green")
            else:
                self.test_section_result.set_attribute(attribute="class", attribute_value="{}".format("glyphicon glyphicon-remove"))
                self.test_section_result.set_attribute(attribute="style", attribute_value="color:red")
        else:
            self.test_section_result.set_attribute(attribute="class", attribute_value=RESULT_COLORS["info"])
        self.test_section_result.set_attribute(attribute="href", attribute_value="#" + self.get_href_id())

        if not self.log_filename:
            log_filename = self.get_href_id()
            log_filename = "/tmp/" + log_filename
            self.log_filename = log_filename
        f = open(self.log_filename, "w")
        self.saved_log = self.saved_log.encode('utf-8', "replace")
        f.write(self.saved_log)
        f.close()
        replacement_logs.append(self.log_filename)
        self.test_log.text = "Replace:" + self.log_filename + ":EndReplace"
        return (self.id, self.summary, "#" + self.get_href_id() + "_top")

    def set_log_anchor(self, log_anchor, checkpoint, result, expected, actual):
        anchor = GenericElement("a")
        anchor.set("name", log_anchor)
        anchor.set("id", log_anchor)
        anchor.text = "checkpoint:" + checkpoint + " Result:" + result + " Expected:" + str(
            expected) + " Actual:" + str(actual)
        anchor.set_attribute(attribute="class", attribute_value=RESULT_COLORS[result.lower()])
        try:
            self.saved_log = self.saved_log.decode('utf-8', "replace") + (get_xml_string(anchor))
        except UnicodeDecodeError as ex:
            print(str(ex))

        except UnicodeEncodeError as ex:
            print(str(ex))

    def get_checkpoint_table(self):
        filter_input = GenericElement("input", id="checkpointfilter__" + self.href_id,
                                      class_name="form-control checkpointfilter")
        filter_input.set("placeholder", "Type Here to filter checkpoints...")
        self.filter_input = filter_input

        checkpoint_table = GenericElement("table")
        checkpoint_table.set_attribute(attribute="width", attribute_value="7%")
        checkpoint_table.set_attribute(attribute="class", attribute_value="table table-nonfluid table-bordered")
        one_row = GenericElement("tr")
        column_names = ['Checkpoint', 'Result', 'Expected', 'Actual']
        for columnName in column_names:
            one_header = GenericElement("th")
            one_header.text = columnName
            one_row.append(one_header)
        checkpoint_table.append(one_row)
        return checkpoint_table

    def add_checkpoint(self, checkpoint, result, expected, actual):
        # Add Row
        self.one_checkpoint = True
        one_row = GenericElement("tr", class_name="checkpointrow_" + self.href_id)

        log_anchor = self.get_href_id() + "log_anchor" + get_timestamp_string()
        self.set_log_anchor(log_anchor=log_anchor, checkpoint=checkpoint, result=result, expected=expected,
                            actual=actual)
        one_table_data = GenericElement("td")
        if checkpoint.startswith("ASSERT"):
            italics_div = GenericElement("i")
            italics_div.text = checkpoint
            one_table_data.append(italics_div)
        else:
            one_table_data.text = checkpoint
        one_row.append(one_table_data)

        one_table_data = GenericElement("td")
        # anchor = GenericElement("a", id="cp_" + log_anchor)
        anchor = GenericElement("div", id="cp_" + log_anchor)

        anchor.set("href", "#" + log_anchor)
        anchor.set("parent-id", self.href_id)
        anchor.text = result
        anchor.set_attribute(attribute="class", attribute_value=RESULT_COLORS[result.lower()] + " checkpointlink pseudo-anchor")
        one_table_data.append(anchor)
        one_table_data.set_attribute(attribute="class", attribute_value=RESULT_COLORS[result.lower()])
        one_row.append(one_table_data)

        one_table_data = GenericElement("td")
        one_table_data.text = expected
        one_row.append(one_table_data)

        one_table_data = GenericElement("td")
        one_table_data.text = str(actual)
        one_row.append(one_table_data)

        self.checkpoint_table.append(one_row)

    def get_test_log(self, log):
        test_log = GenericElement("pre", class_name="plainlogs")
        test_log.text = log
        return test_log

    def log(self, log, newline=True):
        try:
            if newline:
                self.saved_log = self.saved_log.decode('utf-8', "ignore") + "\n" + log
            else:
                self.saved_log = self.saved_log.decode('utf-8', "ignore") + log
        except Exception as ex:
            print "Unable to xmlize"

    def get(self):
        return self


class FunXml:
    _instance = None

    def __init__(self,
                 script_name,
                 log_file="",
                 log_directory="",
                 summary_chart=True,
                 enable_long_summary=True,
                 enable_checkpoint_table=True,
                 enable_bugs=True,
                 variants=None,
                 full_script_path=None,
                 console_log_path=None):
        if FunXml._instance:
            raise Exception("Only one instance of FunXml is permitted")

        self.script_name = script_name
        self.set_log_directory(log_directory=log_directory)
        self.full_script_path = full_script_path
        self.log_file = log_file
        self.variants = variants

        self.enable_long_summary = enable_long_summary
        self.enable_checkpoint_table = enable_checkpoint_table
        self.enable_bugs = enable_bugs
        self.console_log_path = console_log_path

        # Head
        self.head = _XmlHead()

        # Body
        tabs_wrapper = GenericElement("div", class_name="tabs-wrapper")
        self.nav_tab = GenericElement("ul", id="page-tab", class_name="navbar-nav nav")
        # self.nav_tab.set("role", "tablist")

        page_tab1 = self.get_page_tab(name="Results", index=1, href_id="#wrapper")
        page_tab2 = self.get_page_tab(name="Documentation", index=2, href_id="#documentation")
        page_tab3 = self.get_page_tab(name="Script", index=3, href_id="#script")
        # page_tab4 = self.get_page_tab(name="Topology", index=4, href_id="#topology")
        console_tab = None
        if self.console_log_path:
            console_tab = self.get_console_tab()
        page_tab5 = self.get_page_tab(name="FunOS logs/Other logs", index=5, href_id="#aux")

        self.nav_tab.append(page_tab1)
        self.nav_tab.append(page_tab2)
        self.nav_tab.append(page_tab3)
        # self.nav_tab.append(page_tab4)
        if console_tab is not None:
            self.nav_tab.append(console_tab)

        self.nav_tab.append(page_tab5)
        tabs_wrapper.append(self.nav_tab)

        self.tab_content = GenericElement("div", class_name="tab-content card")
        self.documentation_page_content = DocumentationContent(full_script_path=full_script_path)
        self.result_page_content = PageContent(summary_chart=summary_chart,
                                               enable_bugs=enable_bugs,
                                               variants=self.variants)

        self.script_page_content = ScriptContent()
        # self.topology_page_content = TopologyPageContent()
        self.aux_page_content = AuxPageContent()
        self.aux_page_content.get().append(self.result_page_content.get_messages_panel())
        self.tab_content.append(self.result_page_content.get())
        self.tab_content.append(self.documentation_page_content.get())
        self.tab_content.append(self.script_page_content.get())
        # self.tab_content.append(self.topology_page_content.get())
        self.tab_content.append(self.aux_page_content.get())

        self.body = GenericElement('body')
        # self.body.set("ng-app", NG_APP_NAME)

        # self.body.append(self.md_tabs)

        self.body.append(tabs_wrapper)
        # self.body.append(GenericElement("div", id='script_name'))
        self.body.append(self.tab_content)


        # self.body.append(self._get_header_nav())

        # Prepare HTML

        self.html = GenericElement('html')
        self.html.append(self.head)
        self.html.append(self.body)

        self.summary_chart = summary_chart
        self.ts = None
        self.console_log_path = None

    def set_console_log_path(self, console_log_path):
        self.console_log_path = console_log_path

    def add_message(self, message):
        self.result_page_content.add_message(message=message)

    def add_auxillary_file(self, description, auxillary_file):
        self.aux_page_content.add_file(description=description, filename=auxillary_file)

    def get_console_tab(self):
        tab_li = GenericElement("li", class_name="nav-item")
        console_tab = GenericElement("a")
        console_tab.set("href", self.console_log_path)
        console_tab.text = "Console log"
        tab_li.append(console_tab)
        return tab_li

    def get_page_tab(self, name, index, href_id):
        if index == 1:
            tab_li = GenericElement("li", class_name="nav-item active")
        else:
            tab_li = GenericElement("li", class_name="nav-item")
        tab_a = GenericElement("a", class_name="nav-link")
        tab_a.text = name
        tab_a.set("href", href_id)
        tab_a.set("aria-controls", "{}".format(index))
        tab_a.set("role", "tab")
        tab_a.set("data-toggle", "tab")
        tab_li.append(tab_a)
        return tab_li

    def set_topology_json_filename(self, filename):
        self.topology_page_content.set_topology_json_filename(filename)

    def set_log_directory(self, log_directory):
        self.log_directory = log_directory

    def start_test(self, id, summary, steps):
        self.ts = TestSection(id=id, summary=summary, page_content=self.result_page_content,
                              enable_long_summary=self.enable_long_summary,
                              enable_checkpoint_table=self.enable_checkpoint_table)
        if id != -1 and (id != "-"):
            self.result_page_content.add_panel(self.ts)
            self.documentation_page_content.add(id=id,
                                                summary=summary,
                                                steps=steps)
        return self.ts

    def pretty_print(self):
        s = minidom.parseString(tostring(self.html)).toprettyxml(indent=' ')
        print(s)
        return s

    def get(self):
        s = tostring(self.html)
        s = re.sub(u'[^\n\r\t\x20-\x7f]+', u'', s)
        s = minidom.parseString(s).toprettyxml(indent=' ')
        s = s.replace("<md-tabs>", "<md-tabs md-dynamic-height md-border-bottom>")
        s = s.replace("&amp;", "&").replace("&lt;", "<"). \
            replace("&quot;", "\"").replace("&gt;", ">")
        return s

    def get_xml_filename(self):
        filename = self.log_directory + "/" + self.log_file
        # filename = filename.replace(".py", ".html")
        return filename

    def end_test(self, result, bugs=None):
        (id, summary, href) = self.ts.end_test(result=result, bugs=bugs)
        self.result_page_content.start_test(id=id, result=result, bugs=bugs, summary=summary, href=href)

    def get_replacement_log(self, line):
        m = re.search(r'Replace:(.*):EndReplace', line)
        if m:
            log_filename = m.group(1)
            f = open(log_filename, "r")
            contents = f.read()
            try:
                if "Replace" in line:
                    m = re.search(r'Replace:(.*):EndReplace', line)
                    if m:
                        line = line.replace(m.group(0), contents)
                    # line = re.sub(r'Replace:(.*):EndReplace', contents, line)
                else:
                    line = line
            except Exception as ex:
                contents = re.escape(contents)
                line = re.sub(r'Replace:(.*):EndReplace', contents, line)

            f.close()
            os.remove(log_filename)
            pass

        return line

    def close(self):
        # self.page_content.finalize()
        html = self.get()
        f = open(self.get_xml_filename(), "w")
        for line in html.split("\n"):
            if "Replace" in line:
                line = str(line)
            replacement_log = self.get_replacement_log(line=line)
            f.write(replacement_log + '\n')
        f.close()

    def log(self, log, newline=True):
        if self.ts is not None:
            self.ts.log(log=log, newline=newline)

    def add_checkpoint(self, checkpoint, result, expected, actual):
        if self.ts is not None:
            self.ts.add_checkpoint(checkpoint=checkpoint, result=result, expected=str(expected), actual=str(actual))

    def add_collapsible_tab_panel(self, header, panel_items):
        self.ts.add_collapsible_tab_panel(header=header, panel_items=panel_items)

    def add_collapsible_tab_panel_tables(self, header, panel_items):
        self.ts.add_collapsible_tab_panel_tables(header=header, panel_items=panel_items)

    def set_long_summary(self, long_summary):
        self.ts.set_long_summary(long_summary=long_summary)

FunXml_obj = None

if __name__ == "__main__":
    funxml_obj = FunXml(script_name='TestSuite1',
                        log_directory="/Users/johnabraham/PycharmProjects/test2/Integration/fun_test/fun_test/static/logs/",
                        log_file="fun_xml.py")
    funxml_obj.start_test(id="1", summary="Test1 summary", steps="1\n\2.\3")
    funxml_obj.log(log="Some log")
    funxml_obj.add_collapsible_tab_panel(header="ABC", panel_items={"p" : "Pitem1"})

    table_data_headers = ["Header1", "Header2"]
    table_data_rows = [["1", "2"], ["4", "6"]]
    table_data = {"headers": table_data_headers, "rows": table_data_rows}
    funxml_obj.add_collapsible_tab_panel_tables(header="ABC2", panel_items={"p" : table_data})
    funxml_obj.add_checkpoint(checkpoint="ABC", result="PASSED", expected="0", actual="0")
    funxml_obj.end_test(result="PASSED")
    funxml_obj.close()
