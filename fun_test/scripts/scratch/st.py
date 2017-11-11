
attribute_str = """
<div>
    <label>Label1</label>
    <p>Value</p> 
</div>
"""


table = """
<table>
    <tr>
        <th>Test Script</th>
        <th>Def</th>
    </tr>
</table>
"""

contents = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
<style>
th, td {
    padding: 15px;
    text-align: left;
}
</style>

</head>

<body>
%s
%s
</body>
</html>""" % (attribute_str, table)




#print contents

def get_table(header_list, list_of_rows):
    s = "<table>\n"
    s += "\t<tr>\n"
    for header in header_list:
        s += "\t\t<th>" + header + "</th>\n"
    s += "\t</tr>"
    s += "\n"

    for row in list_of_rows:
        s += "\t<tr>\n"
        s += "\t\t"
        for element in row:
            s += "<td>"
            s += element
            s += "</td>"
        s += "\n\t</tr>\n"
    s += "</table>"


    return s

header_list = ["Column1", "Column2", "Column3"]
list_of_rows = []
list_of_rows.append(["Abc", "Cde", "Abc"])
list_of_rows.append(["Efg", "Hij", "HH"])

print get_table(header_list=header_list, list_of_rows=list_of_rows)