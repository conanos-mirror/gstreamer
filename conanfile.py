from conans import ConanFile, CMake, tools,Meson
import os

class GstreamerConan(ConanFile):
    name = "gstreamer-1.0"
    version = "1.14.4"
    description = "GStreamer open-source multimedia framework core library"
    url = "https://gstreamer.freedesktop.org/"
    homepage = "https://github.com/GStreamer/gstreamer"
    license = "GPLv2+"
    exports = ["COPYING"]
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=True"
    generators = "cmake"
    requires = "libffi/3.3-rc0@conanos/dev","glib/2.58.0@conanos/dev","gobject-introspection/1.58.0@conanos/dev" #gtk-doc-lite
    source_subfolder = "source_subfolder"
    remotes = {'origin': 'https://github.com/GStreamer/gstreamer.git'}

    def source(self):
        #tools.get("{0}/archive/{1}.tar.gz".format(self.homepage, self.version))
        #extracted_dir = self.name.split('-')[0] + "-" + self.version
        #os.rename(extracted_dir, self.source_subfolder)
        
        tools.mkdir(self.source_subfolder)
        with tools.chdir(self.source_subfolder):
            self.run('git init')
            for key, val in self.remotes.items():
                self.run("git remote add %s %s"%(key, val))
            self.run('git fetch --all')
            self.run('git reset --hard %s'%(self.version))
            self.run('git submodule update --init --recursive')


    def build(self):
        with tools.environment_append({"LD_LIBRARY_PATH":'%s/lib'%(self.deps_cpp_info["libffi"].rootpath),
            'PATH':'%s/bin:%s'%(self.deps_cpp_info["gobject-introspection"].rootpath, os.getenv("PATH"))}):
            with tools.chdir(self.source_subfolder):
                meson = Meson(self)
                _defs = { 'prefix':'%s/builddir/install'%(os.getcwd()), 'libdir':'lib',
                          'build_tools':'true', 'disable_gtkdoc':'true', 'library_format': 'shared',
                          'disable_introspection' : 'false', 'disable_libunwind' : 'true',
                        }
                meson.configure(
                    defs=_defs,
                    source_dir = '%s'%(os.getcwd()),
                    build_dir= '%s/builddir'%(os.getcwd()),
                    pkg_config_paths=['%s/lib/pkgconfig'%(self.deps_cpp_info["libffi"].rootpath),
                                      '%s/lib/pkgconfig'%(self.deps_cpp_info["glib"].rootpath),]
                    )
                meson.build(args=['-j2'])
                self.run('ninja -C {0} install'.format(meson.build_dir))

    def package(self):
        if tools.os_info.is_linux:
            with tools.chdir(self.source_subfolder):
                self.copy("*", src="%s/builddir/install"%(os.getcwd()))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

