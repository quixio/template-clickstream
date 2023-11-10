import { Component, OnInit } from '@angular/core';
import { environment } from 'src/environments/environment';
import { User } from './models/user';
import { DataService } from './services/data.service';
import { ConnectionStatus, QuixService } from './services/quix.service';
import { MediaObserver } from '@angular/flex-layout';
import { FormControl } from '@angular/forms';
import { EventData } from './models/eventData';
import { actionWords, adjectives, nouns } from './constants/words';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {

  ages = Array.from({length: 48}, (_, i) => i + 18);
  ageControl = new FormControl(this.ages[0]);

  genders = ["Female", "Male", "Unknown"]
  genderControl = new FormControl(this.genders[0]);

  workspaceId: string;
  deploymentId: string;
  ungatedToken: string;
  userId: string;
  user: User;
  constructor(private quixService: QuixService, private dataService: DataService, public media: MediaObserver) {}

  ngOnInit(): void {
    this.user = {
      userId: this.generateUniqueWords(),
      gender: this.genderControl.value || "Female",
      age: this.ageControl.value || 18
    };

    this.dataService.user = this.user;
    const topicId = this.quixService.workspaceId + '-' + this.quixService.offersTopic;
    this.quixService.subscribeToEvent(topicId, this.userId, "offer");

    this.workspaceId = this.quixService.workspaceId;
    this.ungatedToken = this.quixService.ungatedToken;
    this.deploymentId = environment.DEPLOYMENT_ID || '';

    this.quixService.eventDataReceived.subscribe((event: EventData) => {
      this.dataService.openDialog(event)
    });

    this.quixService.readerConnStatusChanged$.subscribe((status) => {
      if (status !== ConnectionStatus.Connected) return;
      this.ageControl.setValue(this.dataService.user.age)
    });

    this.ageControl.valueChanges.subscribe((age) => {
      this.user.age = age || 18;
    });

    this.genderControl.valueChanges.subscribe((gender) => {
      this.user.gender = gender || "Female";
    });
  }

  toggleSidenav(isOpen: boolean): void {
    this.dataService.isSidenavOpen$.next(isOpen);
  }

  generateUniqueWords(): string {
    const uniqueWords: string[] = [];

    while (uniqueWords.length < 3) {
      let randomWord: string;

      if (uniqueWords.length === 0) {
        const randomIndex = Math.floor(Math.random() * adjectives.length);
        randomWord = adjectives[randomIndex];
      } else if (uniqueWords.length === 1) {
        const randomIndex = Math.floor(Math.random() * nouns.length);
        randomWord = nouns[randomIndex];
      } else {
        const randomIndex = Math.floor(Math.random() * actionWords.length);
        randomWord = actionWords[randomIndex];
      }

      if (!uniqueWords.includes(randomWord)) {
        uniqueWords.push(randomWord);
      }
    }

    return uniqueWords.join('-');
  }
}
