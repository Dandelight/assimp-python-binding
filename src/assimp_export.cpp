#include <assimp/postprocess.h>
#include <assimp/scene.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <assimp/Exporter.hpp>
#include <assimp/Importer.hpp>

class AssimpExportWrapper {
 private:
  Assimp::Importer importer;
  Assimp::Exporter exporter;

 public:
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
    // 导入USDZ文件
    const aiScene* scene =
        importer.ReadFile(usdzFile, aiProcess_Triangulate | aiProcess_FlipUVs |
                                        aiProcess_GenSmoothNormals |
                                        aiProcess_JoinIdenticalVertices);

    if (!scene || scene->mFlags & AI_SCENE_FLAGS_INCOMPLETE ||
        !scene->mRootNode) {
      return false;
    }

    // 导出为OBJ
    aiReturn result = exporter.Export(scene, "obj", objFile);
    return result == AI_SUCCESS;
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
      .def(pybind11::init<>())
      .def("get_supported_formats", &AssimpExportWrapper::getSupportedFormats)
      .def("usdz_to_obj", &AssimpExportWrapper::usdzToObj)
      .def("get_last_error", &AssimpExportWrapper::getLastError);
}
