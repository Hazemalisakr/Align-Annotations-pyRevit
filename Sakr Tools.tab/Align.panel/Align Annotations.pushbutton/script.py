# -*- coding: utf-8 -*-
__title__ = 'Align\nAnnotations'
__author__ = 'Sakr'
__doc__ = 'Select multiple annotations (tags, text notes, etc.) and align them horizontally or vertically.'

import os
from pyrevit import revit, DB, forms, script
from Autodesk.Revit.UI.Selection import ObjectType
from Autodesk.Revit.Exceptions import OperationCanceledException

doc = revit.doc
uidoc = revit.uidoc
active_view = doc.ActiveView

def get_annotation_pt(elem):
    """Return the XYZ point of a supported annotation element."""
    if isinstance(elem, DB.TextNote):
        return elem.Coord
    if isinstance(elem, (DB.IndependentTag, DB.SpatialElementTag)):
        return elem.TagHeadPosition
    if hasattr(elem, "TagHeadPosition"):
        return elem.TagHeadPosition
    if hasattr(elem, "Location") and hasattr(elem.Location, "Point") and elem.Location.Point:
        return elem.Location.Point
    return None

class AlignDialog(forms.WPFWindow):
    """Branded WPF dialog for Align Annotations settings."""

    def __init__(self):
        xaml_path = os.path.join(
            os.path.dirname(__file__), 'AlignDialog.xaml')
        forms.WPFWindow.__init__(self, xaml_path)
        self.result = None
        self.btn_ok.Click += self.ok_click
        self.btn_cancel.Click += self.cancel_click

    @property
    def is_horizontal(self):
        return self.rb_horizontal.IsChecked

    @property
    def use_average(self):
        return self.rb_average.IsChecked

    def ok_click(self, sender, args):
        self.result = "ok"
        self.Close()

    def cancel_click(self, sender, args):
        self.result = None
        self.Close()


# Guard against sheet view
if isinstance(active_view, DB.ViewSheet):
    forms.alert("You are on a Sheet view. Please open the floor plan view directly.", exitscript=True)

# Get selected elements
selected_ids = uidoc.Selection.GetElementIds()

supported = (DB.TextNote, DB.IndependentTag, DB.SpatialElementTag)
annotations = []
for eid in selected_ids:
    elem = doc.GetElement(eid)
    if isinstance(elem, supported):
        pt = get_annotation_pt(elem)
        if pt is not None:
            annotations.append((elem, pt))

if not annotations:
    forms.alert('Please select some supported annotations first.', exitscript=True)

if len(annotations) < 2:
    forms.alert('Please select at least two annotations to align.', exitscript=True)

# Show branded dialog
dialog = AlignDialog()
dialog.ShowDialog()

if dialog.result is None:
    script.exit()

horizontal = dialog.is_horizontal
use_average = dialog.use_average

# Use view-relative axes to support rotated views!
view_up = active_view.UpDirection.Normalize()
view_right = active_view.RightDirection.Normalize()
proj_vector = view_up if horizontal else view_right

target_scalar = None

if dialog.rb_average.IsChecked:
    target_scalar = sum(pt.DotProduct(proj_vector) for _, pt in annotations) / len(annotations)
elif dialog.rb_auto.IsChecked:
    # Auto-Anchor: Left-most for Horizontal, Top-most for Vertical
    if horizontal:
        ref_elem, ref_pt = min(annotations, key=lambda x: x[1].DotProduct(view_right))
    else:
        ref_elem, ref_pt = max(annotations, key=lambda x: x[1].DotProduct(view_up))
    target_scalar = ref_pt.DotProduct(proj_vector)
else:
    # Pick Reference on Screen
    try:
        ref_ref = uidoc.Selection.PickObject(
            ObjectType.Element, 
            "Click the exact reference tag on the screen that you want to align to"
        )
        ref_elem = doc.GetElement(ref_ref.ElementId)
        ref_pt = get_annotation_pt(ref_elem)
        if ref_pt is None:
            forms.alert("Unable to read position of the reference element.", exitscript=True)
        else:
            target_scalar = ref_pt.DotProduct(proj_vector)
    except OperationCanceledException:
        script.exit()
    except Exception as ex:
        forms.alert("Reference element selection failed: " + str(ex), exitscript=True)

if target_scalar is None:
    script.exit()

# Perform the alignment inside a transaction
skipped = []
with revit.Transaction('Align Annotations'):
    for elem, pt in annotations:
        if hasattr(elem, "Pinned") and elem.Pinned:
            continue
            
        cur_scalar = pt.DotProduct(proj_vector)
        distance = target_scalar - cur_scalar
        if abs(distance) < 0.0005:
            continue
            
        delta = proj_vector.Multiply(distance)
        new_pt = pt.Add(delta)
        
        try:
            if isinstance(elem, (DB.SpatialElementTag, DB.IndependentTag)):
                if hasattr(elem, "HasLeader") and not elem.HasLeader:
                    # Move via Location.Point for leaderless tags to prevent silent failures or leader sprouting
                    try:
                        elem.Location.Point = new_pt
                    except Exception:
                        skipped.append((elem.Id, "Target point falls outside the 3D room boundary. Revit strictly forbids leaderless tags outside their host rooms."))
                else:
                    elem.TagHeadPosition = new_pt
            elif isinstance(elem, DB.TextNote):
                elem.Coord = new_pt
            else:
                DB.ElementTransformUtils.MoveElement(doc, elem.Id, delta)
        except Exception as ex:
            skipped.append((elem.Id, str(ex)))

if skipped:
    msg = ["Some elements could not be aligned. Revit blocked them because:"]
    for eid, reason in skipped:
        msg.append(" - ElementId {}: {}".format(eid.IntegerValue, reason))
    forms.alert("\n".join(msg))
