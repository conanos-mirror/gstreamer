from conans import ConanFile, CMake, tools,Meson
from conanos.build import config_scheme
import os

class GstreamerConan(ConanFile):
    name = "gstreamer"
    version = "1.14.4"
    description = "GStreamer open-source multimedia framework core library"
    url = "https://github.com/conanos/gstreamer"
    homepage = "https://github.com/GStreamer/gstreamer"
    license = "GPLv2+"
    patch = "gst-debugutils-characters-errorcode.patch"
    exports = ["COPYING", patch]
    generators = "gcc","visual_studio"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        'fPIC': [True, False]
    }
    default_options = { 'shared': False, 'fPIC': True }
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"    

    def requirements(self):
        self.requires.add("glib/2.58.1@conanos/stable")
        self.requires.add("gtk-doc-lite/1.29@conanos/stable")

        config_scheme(self)
    
    def build_requirements(self):
        self.build_requires("libffi/3.299999@conanos/stable")
        self.build_requires("zlib/1.2.11@conanos/stable")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
    
    def configure(self):
        del self.settings.compiler.libcxx

    def source(self):
        remotes = {'origin': 'https://github.com/GStreamer/gstreamer.git'}
        extracted_dir = self.name + "-" + self.version
        tools.mkdir(extracted_dir)
        with tools.chdir(extracted_dir):
            self.run('git init')
            for key, val in remotes.items():
                self.run("git remote add %s %s"%(key, val))
            self.run('git fetch --all')
            self.run('git reset --hard %s'%(self.version))
            self.run('git submodule update --init --recursive')
        if self.settings.os == "Windows":
            tools.patch(patch_file=self.patch)
        os.rename(extracted_dir, self._source_subfolder)

        #url_ = 'https://github.com/GStreamer/gstreamer/archive/{version}.tar.gz'.format(version=self.version)
        #tools.get(url_)
        #if self.settings.os == "Windows":
        #    tools.patch(patch_file=self.patch)
        #extracted_dir = self.name + "-" + self.version
        #os.rename(extracted_dir, self._source_subfolder)        


    def build(self):
        pkg_config_paths=[ os.path.join(self.deps_cpp_info[i].rootpath, "lib", "pkgconfig") for i in ["glib","gtk-doc-lite","libffi","zlib"] ]
        binpath=[ os.path.join(self.deps_cpp_info[i].rootpath, "bin") for i in ["glib","gtk-doc-lite","libffi","zlib"] ]
        prefix = os.path.join(self.build_folder, self._build_subfolder, "install")
        libpath = [ os.path.join(self.deps_cpp_info[i].rootpath, "lib") for i in ["libffi"] ]
        meson = Meson(self)
        defs = {'prefix' : prefix, 'disable_libunwind':'true','disable_introspection':'true'}
        defs['library_format'] = 'shared' if self.options.shared else 'static'
        if self.settings.os == "Linux":
            defs.update({'libdir':'lib'})
        if self.settings.os == 'Windows':
            with tools.environment_append({
                'PATH' : os.pathsep.join(binpath + [os.getenv('PATH')])
                }):
                meson.configure(defs=defs,source_dir=self._source_subfolder, build_dir=self._build_subfolder,
                                pkg_config_paths=pkg_config_paths)
                meson.build()
                self.run('ninja -C {0} install'.format(meson.build_dir))
        if self.settings.os == "Linux":
            defs.update({'disable_gtkdoc':'true'})
            with tools.environment_append({
                'PATH' : os.pathsep.join(binpath + [os.getenv('PATH')]),
                'LD_LIBRARY_PATH' : os.pathsep.join(libpath),
                }):
                meson.configure(defs=defs,source_dir=self._source_subfolder, build_dir=self._build_subfolder,
                                pkg_config_paths=pkg_config_paths)
                meson.build()
                self.run('ninja -C {0} install'.format(meson.build_dir))

    def package(self):
        self.copy("*", dst=self.package_folder, src=os.path.join(self.build_folder,self._build_subfolder, "install"))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

