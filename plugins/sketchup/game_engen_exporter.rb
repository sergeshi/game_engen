# frozen_string_literal: true
# GAME ENGEN SketchUp bridge — best-effort export menu helper.
require 'sketchup.rb'
module GameEngen
  module Exporter
    extend self
    def export_model
      model = Sketchup.active_model
      return UI.messagebox('No active SketchUp model.') unless model
      path = UI.savepanel('Export model for GAME ENGEN', '', 'game-engen-export.dae')
      return unless path
      begin
        ok = model.export(path, {})
        if ok
          UI.messagebox("Exported model:\n#{path}\n\nIf the browser editor cannot import this format, convert it to GLB/glTF or OBJ first.")
        else
          UI.messagebox('Export failed. Try File → Export → 3D Model and choose a format supported by your SketchUp version.')
        end
      rescue StandardError => e
        UI.messagebox("Export failed: #{e.message}")
      end
    end
    unless file_loaded?(__FILE__)
      UI.menu('Extensions').add_item('GAME ENGEN: Export model…') { export_model }
      file_loaded(__FILE__)
    end
  end
end
