ssh bc-ui "sudo apt update && sudo apt upgrade -y"
sleep 3
ssh bc-hq "sudo apt update && sudo apt upgrade -y"
sleep 3
ssh bc-power "sudo apt update && sudo apt upgrade -y"
sleep 3
ssh bc-water "sudo apt update && sudo apt upgrade -y"
sleep 3
ssh bc-veilleuse "sudo apt update && sudo apt upgrade -y"
sleep 3
ssh bc-water "sudo apt update && sudo apt upgrade -y"
sleep 3
ssh bc-watch "sudo apt update && sudo apt upgrade -y"
