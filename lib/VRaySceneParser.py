#
# V-Ray For Blender
#
# http://chaosgroup.com
#
# Author: Andrei Izrantcev
# E-Mail: andrei.izrantcev@chaosgroup.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# All Rights Reserved. V-Ray(R) is a registered trademark of Chaos Software.
#

from .pyparsing import Literal, CaselessLiteral, Word, Keyword
from .pyparsing import OneOrMore, ZeroOrMore, Group, Combine, Optional
from .pyparsing import alphas, nums, alphanums, quotedString, delimitedList, quotedString
from .pyparsing import restOfLine, cStyleComment


# Returns parsed description dict
#
def getPluginDesc(s,loc,toks):
    plType  = toks[0][0]
    plName  = toks[0][1]
    plAttrs = toks[0][2]

    attrs = {}
    for plAttr in plAttrs:
        attrs[plAttr[0]] = plAttr[1]

    return {
        "ID" : plType,
        "Name" : plName,
        "Attributes" : attrs,
    }

# Converters
#
to_int    = lambda s,l,t: int(t[0])
to_float  = lambda s,l,t: float(t[0])
to_vector = lambda s,l,t: tuple(t[0])
no_quotes = lambda s,l,t: t[0][1:-1]

# Generic syntax
#
lparen = Literal("(").suppress()
rparen = Literal(")").suppress()
lbrace = Literal("{").suppress()
rbrace = Literal("}").suppress()
equals = Literal("=").suppress()
semi   = Literal(";").suppress()
dot    = Literal(".")
comma  = Literal(",")

# Keywords
#
Color = Keyword("Color").suppress()
AColor = Keyword("AColor").suppress()

# Values
#
real = Combine(Word(nums+"+-", nums) + dot + Optional( Word(nums) ) + Optional(CaselessLiteral("E") + Word(nums+"+-",nums) ) ).setParseAction(to_float)
integer = Word(nums+"+-", nums).setParseAction(to_int)
color = Color + lparen + Group(delimitedList(real)).setParseAction(to_vector) + rparen
acolor = AColor + lparen + Group(delimitedList(real)).setParseAction(to_vector) + rparen

# Plugin Attribute
#
attrName  = Word(alphas+"_")
attrValue = integer ^ real ^ color ^ acolor ^ Word(alphanums) ^ quotedString.setParseAction(no_quotes)

pluginAttr = Group(attrName + equals + attrValue + semi)

# Plugin
#
pluginType = Word(alphas)
pluginName = Word(alphas+"@")
pluginDesc = Group(pluginType + pluginName + lbrace + Group(ZeroOrMore(pluginAttr)) + rbrace).setParseAction(getPluginDesc)
pluginDesc.ignore("//"+restOfLine)
pluginDesc.ignore(cStyleComment)

# Scene
#
sceneDesc = OneOrMore(pluginDesc)
sceneDesc.ignore("//"+restOfLine)
sceneDesc.ignore(cStyleComment)


def ParseVrscene(filepath):
    return sceneDesc.parseString(open(filepath, "r").read())


def GetMaterialsNames(filepath):
    vrscenePlugins = ParseVrscene(filepath)

    materialPluginNames = []
    for plug in vrscenePlugins:
        if plug['ID'].startswith("Mtl"):
            if plug['Name'] == 'MANOMATERIALISSET':
                continue
            materialPluginNames.append(plug['Name'])

    return materialPluginNames


if __name__ == '__main__':
    print(GetMaterialsNames("/tmp/vrayblender_bdancer/scene_materials.vrscene"))
