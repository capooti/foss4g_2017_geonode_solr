# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/xenial64"
  config.vm.box_url = "ubuntu/xenial64"
  config.vm.network :forwarded_port, guest: 80, host: 8081
  config.vm.network :forwarded_port, guest: 5555, host: 5555
  config.vm.network :forwarded_port, guest: 8000, host: 8000
  config.vm.network :forwarded_port, guest: 8080, host: 8080
  config.vm.network :forwarded_port, guest: 8983, host: 8983


  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--name", "geonode-solr-foss4g-workshop", "--memory", "4096"]
  end

  config.vm.synced_folder "", "/workshop"

end
