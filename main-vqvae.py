import torch
import torchvision
from torchvision.utils import save_image

import matplotlib.pyplot as plt
from tqdm import tqdm

import argparse
from math import sqrt

from trainer import Trainer
from hps import HPS
from helper import NoLabelImageFolder, get_device, get_parameter_count

def get_dataset(task: str, cfg):
    if task == 'ffhq1024':
        transforms = torchvision.transforms.Compose([
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5]),
        ])
        dataset = torchvision.datasets.ImageFolder('data/ffhq1024', transform=transforms)
        nb_test = int(len(dataset) * cfg.test_size)
        nb_train = len(dataset) - nb_test
        train_dataset, test_dataset = torch.utils.data.random_split(dataset, [nb_train, nb_test])
    elif task == 'ffhq256':
        transforms = torchvision.transforms.Compose([
            torchvision.transforms.Resize(256),
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5]),
        ])
        dataset = torchvision.datasets.ImageFolder('data/ffhq1024', transform=transforms)
        nb_test = int(len(dataset) * cfg.test_size)
        nb_train = len(dataset) - nb_test
        train_dataset, test_dataset = torch.utils.data.random_split(dataset, [nb_train, nb_test])
    elif task == 'ffhq128':
        transforms = torchvision.transforms.Compose([
            torchvision.transforms.Resize(128),
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5]),
        ])
        dataset = torchvision.datasets.ImageFolder('data/ffhq1024', transform=transforms)
        nb_test = int(len(dataset) * cfg.test_size)
        nb_train = len(dataset) - nb_test
        train_dataset, test_dataset = torch.utils.data.random_split(dataset, [nb_train, nb_test])
    elif task == 'cifar10':
        transforms = torchvision.transforms.Compose([
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5]),
        ])
        train_dataset = torchvision.datasets.CIFAR10('data', train=True, transform=transforms, download=True)
        test_dataset = torchvision.datasets.CIFAR10('data', train=False, transform=transforms, download=True)
    elif task == 'mnist':
        transforms = torchvision.transforms.Compose([
            torchvision.transforms.ToTensor(),
        ])
        train_dataset = torchvision.datasets.MNIST('data', train=True, transform=transforms, download=True)
        test_dataset = torchvision.datasets.MNIST('data', train=False, transform=transforms, download=True)
    elif task == 'kmnist':
        transforms = torchvision.transforms.Compose([
            torchvision.transforms.ToTensor(),
        ])
        train_dataset = torchvision.datasets.KMNIST('data', train=True, transform=transforms, download=True)
        test_dataset = torchvision.datasets.KMNIST('data', train=False, transform=transforms, download=True)
    else:
        print("> Unknown dataset. Terminating")
        exit()

    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=cfg.batch_size, num_workers=cfg.nb_workers, shuffle=True)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=cfg.batch_size, num_workers=cfg.nb_workers, shuffle=False)

    return train_loader, test_loader

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cpu', action='store_true')
    parser.add_argument('--task', type=str, default='cifar10')
    args = parser.parse_args()
    cfg = HPS[args.task]

    print(f"Loading {cfg.display_name} dataset")
    train_loader, test_loader = get_dataset(args.task, cfg)

    print(f"Initialising VQ-VAE-2 model")
    trainer = Trainer(cfg, args.cpu)
    # device = get_device(args.cpu)
    # net = VQVAE(in_channels=cfg.in_channels, 
                # hidden_channels=cfg.hidden_channels, 
                # embed_dim=cfg.embed_dim, 
                # nb_entries=cfg.nb_entries, 
                # nb_levels=cfg.nb_levels, 
                # scaling_rates=cfg.scaling_rates).to(device)
    # optim = torch.optim.Adam(net.parameters(), lr=cfg.learning_rate)
    print(f"Number of trainable parameters: {get_parameter_count(trainer.net)}")

    for eid in range(cfg.max_epochs):
        epoch_loss, epoch_r_loss, epoch_l_loss = 0.0, 0.0, 0.0
        pb = tqdm(train_loader)
        # net.train()
        for i, (x, _) in enumerate(pb):
            loss, r_loss, l_loss = trainer.train(x)
            epoch_loss += loss
            epoch_r_loss += r_loss
            epoch_l_loss += l_loss
            pb.set_description(f"training_loss: {epoch_loss / (i+1)} [r_loss: {epoch_r_loss/ (i+1)}, l_loss: {epoch_l_loss / (i+1)}]")
        print(f"Training loss: {epoch_loss / len(train_loader)}")
        
        epoch_loss, epoch_r_loss, epoch_l_loss = 0.0, 0.0, 0.0
        for i, (x, _) in enumerate(test_loader):
            loss, r_loss, l_loss = trainer.eval(x)
            epoch_loss += loss
            epoch_r_loss += r_loss
            epoch_l_loss += l_loss

        if eid % cfg.image_frequency == 0:
            save_image(y, f"samples/recon-{eid}.png", nrow=int(sqrt(cfg.batch_size)), normalize=True, value_range=(-1,1))

    print(f"Evaluation loss: {epoch_loss / len(test_loader)}")
    print()