while :
do
	python seopibot_main.py
	if [ $? -eq 0 ]; then
		echo "Exiting."
		break
	fi
	if [ $? -eq 1 ]; then
		echo "Restarting.."
	fi
done

