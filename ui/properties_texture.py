'''

  V-Ray/Blender 2.5

  http://vray.cgdo.ru

  Time-stamp: "Tuesday, 15 March 2011 [13:34]"

  Author: Andrey M. Izrantsev (aka bdancer)
  E-Mail: izrantsev@cgdo.ru

  This program is free software; you can redistribute it and/or
  modify it under the terms of the GNU General Public License
  as published by the Free Software Foundation; either version 2
  of the License, or (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.

  All Rights Reserved. V-Ray(R) is a registered trademark of Chaos Software.

'''


''' Blender modules '''
import bpy

''' vb modules '''
from vb25.utils import *
from vb25.ui.ui import *
from vb25.plugins import *


class VRAY_TP_context(VRayTexturePanel, bpy.types.Panel):
	bl_label       = ""
	bl_options     = {'HIDE_HEADER'}

	COMPAT_ENGINES = {'VRAY_RENDER','VRAY_RENDER_PREVIEW'}

	@classmethod
	def poll(cls, context):
		# If texture used in nodes
		if not hasattr(context, 'texture_slot'):
			return False
		return (context.material or context.world or context.lamp or context.brush or context.texture) and engine_poll(cls, context)

	def draw(self, context):
		layout= self.layout
		
		node=    context.texture_node
		space=   context.space_data
		idblock= context_tex_datablock(context)
		pin_id=  space.pin_id

		slot= getattr(context, 'texture_slot', None)
		tex=  slot.texture if slot else context.texture

		if not isinstance(pin_id, bpy.types.Material):
			pin_id = None

		if not space.use_pin_id:
			layout.prop(space, "texture_context", expand=True)

		tex_collection = (not space.use_pin_id) and (node is None) and (not isinstance(idblock, bpy.types.Brush))

		if tex_collection:
			row = layout.row()

			row.template_list(idblock, "texture_slots", idblock, "active_texture_index", rows=2)

			col = row.column(align=True)
			col.operator("texture.slot_move", text="", icon='TRIA_UP').type = 'UP'
			col.operator("texture.slot_move", text="", icon='TRIA_DOWN').type = 'DOWN'
			col.menu("TEXTURE_MT_specials", icon='DOWNARROW_HLT', text="")

		split = layout.split(percentage=0.65)
		col = split.column()

		if tex_collection:
			col.template_ID(idblock, "active_texture", new="texture.new")
		elif node:
			col.template_ID(node, "texture", new="texture.new")
		elif idblock:
			col.template_ID(idblock, "texture", new="texture.new")

		if pin_id:
			col.template_ID(space, "pin_id")

		col = split.column()

		if tex:
			split = layout.split(percentage=0.2)

			if tex.use_nodes:

				if slot:
					split.label(text="Output:")
					split.prop(slot, "output_node", text="")

			else:
				split.label(text="Texture:")
				split.prop(tex, 'type', text="")
				if tex.type == 'VRAY':
					split= layout.split()
					col= split.column()
					col.prop(tex.vray, 'type', text="Type")


import properties_texture
properties_texture.TEXTURE_PT_preview.COMPAT_ENGINES.add('VRAY_RENDER')
properties_texture.TEXTURE_PT_preview.COMPAT_ENGINES.add('VRAY_RENDER_PREVIEW')
properties_texture.TEXTURE_PT_image.COMPAT_ENGINES.add('VRAY_RENDER')
properties_texture.TEXTURE_PT_image.COMPAT_ENGINES.add('VRAY_RENDER_PREVIEW')
del properties_texture


class VRAY_TP_influence(VRayTexturePanel, bpy.types.Panel):
	bl_label = "Influence"
	
	COMPAT_ENGINES = {'VRAY_RENDER','VRAY_RENDER_PREVIEW'}

	@classmethod
	def poll(cls, context):
		# If texture used in nodes
		if not hasattr(context, 'texture_slot'):
			return False
		return super().poll(context) and (context.material or context.world or context.lamp or context.brush or context.texture)

	def draw(self, context):
		layout= self.layout
		wide_ui= context.region.width > narrowui

		idblock= context_tex_datablock(context)

		slot=    context.texture_slot
		texture= slot.texture if slot else context.texture

		VRaySlot= texture.vray_slot

		if issubclass(type(idblock), bpy.types.Material):
			material=     context.material
			VRayMaterial= material.vray

			PLUGINS['BRDF'][VRayMaterial.type].influence(context, layout, slot)

			PLUGINS['BRDF']['BRDFBump'].influence(context, layout, slot)

			PLUGINS['GEOMETRY']['GeomDisplacedMesh'].influence(context, layout, slot)

		elif issubclass(type(idblock), bpy.types.Lamp):
			VRayLight= VRaySlot.VRayLight

			split= layout.split()
			col= split.column()
			factor_but(col, VRayLight, 'map_color', 'color_mult', "Color")
			factor_but(col, VRayLight, 'map_shadowColor', 'shadowColor_mult', "Shadow")
			if wide_ui:
				col= split.column()
			factor_but(col, VRayLight, 'map_intensity', 'intensity_mult', "Intensity")

		elif issubclass(type(idblock), bpy.types.World):
			split= layout.split()
			col= split.column()
			col.label(text="Environment:")
			factor_but(col, VRaySlot, 'use_map_env_bg',         'env_bg_factor',         "Background")
			if wide_ui:
				col= split.column()
			col.label(text="Override:")
			factor_but(col, VRaySlot, 'use_map_env_gi',         'env_gi_factor',         "GI")
			factor_but(col, VRaySlot, 'use_map_env_reflection', 'env_reflection_factor', "Reflections")
			factor_but(col, VRaySlot, 'use_map_env_refraction', 'env_refraction_factor', "Refractions")

		layout.separator()

		split= layout.split()
		col= split.column()
		col.prop(VRaySlot,'blend_mode',text="Blend")
		if wide_ui:
			col= split.column()
		col.prop(slot,'use_stencil')



class VRAY_TP_displacement(VRayTexturePanel, bpy.types.Panel):
	bl_label = "Displacement"
	
	COMPAT_ENGINES = {'VRAY_RENDER','VRAY_RENDER_PREVIEW'}

	@classmethod
	def poll(cls, context):
		idblock= context_tex_datablock(context)
		if not type(idblock) == bpy.types.Material:
			return False

		texture_slot= getattr(context,'texture_slot',None)
		if not texture_slot:
			return False

		texture= texture_slot.texture
		if not texture:
			return False
		
		VRaySlot= texture.vray_slot
		return VRaySlot.map_displacement and engine_poll(cls, context)

	def draw(self, context):
		layout= self.layout
		wide_ui= context.region.width > narrowui

		texture_slot= getattr(context,'texture_slot',None)
		texture= texture_slot.texture if texture_slot else context.texture

		if texture:
			VRaySlot= texture.vray_slot

			if VRaySlot:
				GeomDisplacedMesh= VRaySlot.GeomDisplacedMesh

				split= layout.split()
				col= split.column()
				col.prop(GeomDisplacedMesh, 'displacement_shift', slider=True)
				col.prop(GeomDisplacedMesh, 'water_level', slider=True)
				col.prop(GeomDisplacedMesh, 'resolution')
				col.prop(GeomDisplacedMesh, 'precision')
				if wide_ui:
					col= split.column()
				col.prop(GeomDisplacedMesh, 'keep_continuity')
				col.prop(GeomDisplacedMesh, 'use_bounds')
				if GeomDisplacedMesh.use_bounds:
					sub= col.row()
					sub.prop(GeomDisplacedMesh, 'min_bound', text="Min")
					sub.prop(GeomDisplacedMesh, 'max_bound', text="Max")
				col.prop(GeomDisplacedMesh, 'filter_texture')
				if GeomDisplacedMesh.filter_texture:
					col.prop(GeomDisplacedMesh, 'filter_blur')

				split= layout.split()
				col= split.column()
				col.prop(GeomDisplacedMesh, 'use_globals')
				if not GeomDisplacedMesh.use_globals:
					split= layout.split()
					col= split.column()
					col.prop(GeomDisplacedMesh, 'edge_length')
					col.prop(GeomDisplacedMesh, 'max_subdivs')
					if wide_ui:
						col= split.column()
					col.prop(GeomDisplacedMesh, 'view_dep')
					col.prop(GeomDisplacedMesh, 'tight_bounds')


class VRAY_TP_bitmap(VRayTexturePanel, bpy.types.Panel):
	bl_label = "Bitmap"

	COMPAT_ENGINES = {'VRAY_RENDER','VRAY_RENDER_PREVIEW'}

	@classmethod
	def poll(cls, context):
		tex= context.texture
		return super().poll(context) and (tex.type == 'IMAGE' and tex.image)

	def draw(self, context):
		layout= self.layout
		wide_ui= context.region.width > narrowui

		slot= getattr(context,'texture_slot',None)
		tex= slot.texture if slot else context.texture

		BitmapBuffer= tex.image.vray.BitmapBuffer

		split= layout.split()
		col= split.column()
		col.prop(BitmapBuffer, 'color_space')

		split= layout.split()
		col= split.column()
		col.prop(BitmapBuffer, 'filter_type', text="Filter")
		if BitmapBuffer.filter_type != 'NONE':
			col.prop(BitmapBuffer, 'filter_blur')
		if BitmapBuffer.filter_type == 'MIPMAP':
			col.prop(BitmapBuffer, 'interpolation', text="Interp.")
		if wide_ui:
			col= split.column()
		col.prop(BitmapBuffer, 'use_input_gamma')
		if not BitmapBuffer.use_input_gamma:
			col.prop(BitmapBuffer, 'gamma')
			#col.prop(BitmapBuffer, 'gamma_correct')
		col.prop(BitmapBuffer, 'allow_negative_colors')
		col.prop(BitmapBuffer, 'use_data_window')

