# ruff: noqa
import datetime
import io
import os
from pprint import pprint
from random import sample
import logging as log

import librosa
import noisereduce as nr
import requests
import soundfile as sf
import whisper
from pydub import AudioSegment
from pydub.silence import split_on_silence

TEMP_FOLDER = "temp_audio"


def remove_noise(filename):
    # file_path.seek(0)
    data, rate = librosa.load(filename, sr=None)

    # Perform noise reduction
    reduced_noise_audio = nr.reduce_noise(y=data, sr=rate)

    # Construct the output filename by adding '-nc' before the file extension
    output_filename = filename.rsplit(".", 1)[0] + "_nc.wav"

    # Save the processed audio data as a .wav file
    sf.write(output_filename, reduced_noise_audio, rate, format="wav")

    return output_filename


def get_file_type(filename):
    _, file_extension = os.path.splitext(filename)
    return file_extension.lower()


def remove_silence_from_audio(filename, silence_thresh=-15, min_silence_len=1000):
    ###### Remove noise from the audio
    noise_reduced_filename = remove_noise(filename)
    # file_type = get_file_type(noise_reduced_stream)
    # # print(file_type)

    # Load the noise-reducced audio file
    audio = AudioSegment.from_file(noise_reduced_filename, format="wav")
    ##################################

    # temp_folder_name = "temp_audio"
    # temp_file_name = f"{file}.wav"
    # temp_file_path = os.path.join(temp_folder_name, temp_file_name)
    # # print("file", file)

    # audio = AudioSegment.from_file(temp_file_path, format="wav")

    # Split the audio on silence
    audio_chunks = split_on_silence(
        audio,
        min_silence_len=min_silence_len,  # minimum length of silence to be considered as a break
        silence_thresh=silence_thresh,  # silence threshold
        seek_step=10,  # step size for iterating over the audio
    )

    # Combine non-silent audio chunks
    combined_audio = AudioSegment.empty()
    for i, chunk in enumerate(audio_chunks):
        combined_audio += chunk

    print("===== Processing audio file =====")
    output_filename = filename.rsplit(".", 1)[0] + "_p.mp3"  # processed
    # Export the processed audio
    combined_audio.export(output_filename, format="mp3")
    print("===== Finished processing audio file =====")
    return output_filename


def append_to_text_file(input_string, processed_file, filename="text_archive.txt"):
    with open(filename, "a") as file:
        file.write(f"{processed_file}" + "\n")
        file.write(input_string + "\n")


def ai_translate(audio_file_path):
    model = whisper.load_model("medium.en")
    print(f"STT for {audio_file_path}")
    result = model.transcribe(audio_file_path, fp16=False)

    pprint(result)
    # something not good here
    append_to_text_file(result["text"], audio_file_path)
    print(f"STT DONE for {audio_file_path}")


def format_datetime_for_url(date=None):
    # parse input date, for Url
    if date is None:
        date = datetime.datetime.now().date()

    datetime_obj = datetime.datetime(date.year, date.month, date.day)

    formatted_date = date.strftime("%m/%d/%Y")
    timestamp = int(datetime_obj.timestamp())

    return formatted_date, timestamp


def get_first_element(list):
    first_elem = list["data"][0] if list["data"] else None
    return first_elem


def extract_ids_from_archive(archive):
    return [item[0] for item in archive["data"]] if "data" in archive else None


def get_full_day_archives(session, feedId, date=None):
    # default to yesterday
    if date is None:
        date = datetime.now().date() - datetime.timedelta(days=1)
    feed_archive_url = "https://www.broadcastify.com/archives/ajax.php"
    url_date = format_datetime_for_url(date)
    formatted_url = (
        f"{feed_archive_url}?feedId={feedId}&date={url_date[0]}&_={url_date[1]}"
    )

    feed_archive = session.get(formatted_url).json()
    id_list = extract_ids_from_archive(feed_archive)
    return id_list


def save_and_convert_to_wav(file_stream, file_name):
    # download the file as mp3, then convers to wav
    file_stream.seek(0)

    with open(file_name + ".mp3", "wb") as file:
        file.write(file_stream.read())

    # convert MP3 to WAV
    audio = AudioSegment.from_mp3(file_name + ".mp3")
    audio_file_name = os.path.join(TEMP_FOLDER, file_name + ".wav")
    audio.export(audio_file_name, format="wav")
    delete_temp_mp3(file_name)
    return audio_file_name


def delete_temp_mp3(filename):
    mp3_filename = f"{filename}.mp3"
    os.remove(mp3_filename)


def download_archive(session, ar_list):
    base_url = "https://www.broadcastify.com"
    file_list = []
    for archive_id in ar_list:
        response = session.get(
            f"{base_url}/archives/downloadv2/{archive_id}"
        )  # download the mp3 file
        filename = save_and_convert_to_wav(
            io.BytesIO(response.content), archive_id
        )  # save and convert to wav
        file_list.append(filename)
    return file_list


def process_archive_silence(file_list):
    for idx, filename in enumerate(file_list):
        file_list[idx] = remove_silence_from_audio(filename, silence_thresh=-30)
    return file_list


def stt_archive(file_list):
    for filename in file_list:
        try:
            ai_translate(filename)
        except Exception as e:
            log.error(f"Failed to translate file {filename}", e)


def parse_date_archive(date=datetime.datetime.now()):
    username = "alertai"
    password = "Var+(n42421799)"
    action = "auth"
    redirect = "https://www.broadcastify.com/"

    s = requests.Session()

    base_url = "https://www.broadcastify.com"
    login_url = "https://m.broadcastify.com/login/"
    payload = {
        "username": username,
        "password": password,
        "action": action,
        "redirect": redirect,
    }
    s.post(
        login_url,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    # verify if this is successful
    if s.cookies.get("bcfyuser1", default=None) is None:
        print("Login failed")
        return
    print("Login successful")

    # url_date = parse_datetime_for_url("01/12/2024")
    # feed_archive_url = "https://www.broadcastify.com/archives/ajax.php"
    # feedId = 25306
    # formatted_url = (
    #     f"{feed_archive_url}?feedId={feedId}&date={url_date[0]}&_={url_date[1]}"
    # )
    # feed_archive = s.get(formatted_url).json()
    # first_elem = get_first_element(feed_archive)
    # print("firstElem", first_elem)
    # print("feedArchive", feed_archive)
    # archive_id = first_elem[0]
    # response = s.get(f"{base_url}/archives/downloadv2/{archive_id}")    # download the mp3 file
    # save_and_convert_to_wav(io.BytesIO(response.content), archive_id)   # save and convert to wav

    ###########################################
    # # here we apply noise cancelling if needed
    # temp_folder_name = "temp_audio"
    # temp_file_name = f"{archive_id}.wav"
    # temp_file_path = os.path.join(temp_folder_name, temp_file_name)

    # # remove silence only for first feed
    # remove_silence_from_audio(temp_file_path)
    ############################################

    # feed
    # 25306 - Alsip Fire
    # 25831 - Calumet Park Fire
    archive_id_list = get_full_day_archives(
        s,
        feedId=25831,
        date=date,
    )
    # take 3 random ids
    # archive_id_list = sample(archive_id_list, 3)
    print(archive_id_list)

    # download full day archive
    file_list = download_archive(s, archive_id_list)

    # process temp_audio files, to remove silence
    file_list = process_archive_silence(file_list)
    print(file_list)
    # whisper STT archive
    stt_archive(file_list)


def main():
    # parse last 10 days of data
    for i in range(1, 10):
        parse_date_archive(datetime.datetime.now() - datetime.timedelta(days=i))


if __name__ == "__main__":
    if not os.path.isdir(TEMP_FOLDER):
        os.mkdir(TEMP_FOLDER)

    main()
