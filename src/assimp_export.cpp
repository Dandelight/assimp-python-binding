#include <assimp/postprocess.h>
#include <assimp/scene.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <assimp/Exporter.hpp>
#include <assimp/Importer.hpp>
#include <iostream>

class AssimpExportWrapper {
 private:
  Assimp::Importer importer;
  Assimp::Exporter exporter;
  bool enable_logging;

  void log(const std::string& msg) const {
    if (enable_logging) {
      std::cout << "[assimp_export] " << msg << std::endl;
    }
  }

 public:
  AssimpExportWrapper(bool enableLogging = false)
      : enable_logging(enableLogging) {
    if (enable_logging) {
      std::cout << "[assimp_export] Logger enabled" << std::endl;
    }
  }

  std::vector<std::string> getSupportedFormats() {
    std::vector<std::string> formats;
    for (size_t i = 0; i < exporter.GetExportFormatCount(); ++i) {
      const aiExportFormatDesc* desc = exporter.GetExportFormatDescription(i);
      formats.push_back(std::string(desc->id) + " - " +
                        std::string(desc->description));
    }
    return formats;
  }

  bool usdzToObj(const std::string& usdzFile, const std::string& objFile) {
    log("Start converting USDZ -> OBJ");
    log(std::string("Input: ") + usdzFile);
    log(std::string("Output: ") + objFile);

    unsigned int ppFlags = aiProcess_Triangulate | aiProcess_FlipUVs |
                           aiProcess_GenSmoothNormals |
                           aiProcess_JoinIdenticalVertices;

    log("Post-process flags: "
        "Triangulate | FlipUVs | GenSmoothNormals | JoinIdenticalVertices");

    const aiScene* scene = importer.ReadFile(usdzFile, ppFlags);

    if (!scene) {
      std::string err = importer.GetErrorString();
      log(std::string("Import failed: ") +
          (err.empty() ? "<no error string>" : err));
      return false;
    }

    if (scene->mFlags & AI_SCENE_FLAGS_INCOMPLETE) {
      log("Import failed: scene is incomplete (AI_SCENE_FLAGS_INCOMPLETE)");
      log(std::string("Importer error: ") + importer.GetErrorString());
      return false;
    }

    if (!scene->mRootNode) {
      log("Import failed: scene->mRootNode is null");
      log(std::string("Importer error: ") + importer.GetErrorString());
      return false;
    }

    log("Import succeeded.");
    log(std::string("Meshes: ") + std::to_string(scene->mNumMeshes) +
        ", Materials: " + std::to_string(scene->mNumMaterials) +
        ", Textures: " + std::to_string(scene->mNumTextures));

    log("Begin export to OBJ...");
    aiReturn result = exporter.Export(scene, "obj", objFile);

    if (result != AI_SUCCESS) {
      std::string err = exporter.GetErrorString();
      log(std::string("Export failed: ") +
          (err.empty() ? "<no error string>" : err));
      return false;
    }

    log("Export succeeded.");
    return true;
  }

  std::string getLastError() {
    std::string importError = importer.GetErrorString();
    std::string exportError = exporter.GetErrorString();

    if (!importError.empty()) return "Import: " + importError;
    if (!exportError.empty()) return "Export: " + exportError;
    return "";
  }
};

PYBIND11_MODULE(assimp_export_core, m) {
  m.doc() = "Assimp Export Python Binding";

  pybind11::class_<AssimpExportWrapper>(m, "AssimpExporter")
      .def(pybind11::init<bool>(), pybind11::arg("enable_logging") = false)
      .def("get_supported_formats", &AssimpExportWrapper::getSupportedFormats)
      .def("usdz_to_obj", &AssimpExportWrapper::usdzToObj)
      .def("get_last_error", &AssimpExportWrapper::getLastError);
}
