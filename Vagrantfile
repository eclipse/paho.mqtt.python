Vagrant.configure("2") do |config|
  # The base OS 
  config.vm.box = "ubuntu/trusty64"
  config.vm.provision :shell, :inline => "sudo apt-get update"
  
  # Install make, python
  config.vm.provision :shell, :inline => "apt-get install -y make"
  config.vm.provision :shell, :inline => "apt-get install -y python3"

  # reassuring message to complete:
  config.vm.provision "shell", inline: "echo All set!", run: "always"
end
