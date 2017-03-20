Vagrant.configure("2") do |config|
  # The base OS 
  config.vm.box = "ubuntu/trusty64"
  config.vm.provision :shell, :inline => "sudo apt-get update"
  
  # Install make
  config.vm.provision :shell, :inline => "apt-get install -y make"

  # Provision Python 2
  config.vm.provision :shell, :inline => "apt-get upgrade -y python"
  config.vm.provision :shell, :inline => "apt-get install -y python-pip"
  config.vm.provision :shell, :inline => "python -m pip install --upgrade pip"
  config.vm.provision :shell, :inline => "python -m pip install virtualenv"

  # Provision Python 3
  config.vm.provision :shell, :inline => "apt-get install -y python3"
  config.vm.provision :shell, :inline => "apt-get install -y python3-pip"
  config.vm.provision :shell, :inline => "python3 -m pip install --upgrade pip"
  config.vm.provision :shell, :inline => "python3 -m pip install virtualenv"

  # reassuring message to complete:
  config.vm.provision "shell", inline: "echo All set!", run: "always"
end
